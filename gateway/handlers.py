# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2017
# 
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -------------------------------------------------------------------------------
import traceback
import json
import uuid
import nbformat
import tornado
from tornado import gen, web
from .session import Session, SessionManager
from .notebookMgr import NotebookMgr
from .managedClient import ManagedClientPool

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        pass

    def prepare(self):
        """
        Retrieve session for current user
        """
        self.session = SessionManager.instance().get_session(self)
        print("session {}".format(self.session))

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

class ExecuteCodeHandler(BaseHandler):
    """
Common Base Tornado Request Handler class.
Implement generic kernel code execution routine
    """
    @gen.coroutine
    def post(self):
        managed_client = ManagedClientPool.instance().get()
        with (yield managed_client.lock.acquire()):
            try:
                response = yield managed_client.execute_code(self.request.body.decode('utf-8'))
                self.write(response)
            except:
                traceback.print_exc()
            finally:
                self.finish()

class TestHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        self.set_header('Content-Type', 'text/html')
        self.set_status(200)
        code = """
from pixiedust.display.app import *
@PixieApp
class Test():
    globalHomes = None
    def setup(self):
        if Test.globalHomes is None:
            Test.globalHomes = pixiedust.sampleData(6)
        self.homes = Test.globalHomes
    @route()
    def main(self):
        return \"\"\"{}\"\"\"
Test().run()
        """.format("""
        <div class="row">
            <div class="col-sm-2">
                <button pd_entity="homes" pd_target="target{{prefix}}" type="button">
                    Bar Chart
                    <pd_options>
                        {
                          "handlerId": "barChart",
                          "keyFields": "CITY",
                          "valueFields": "PRICE",
                          "aggregation": "AVG",
                          "rowCount": "500",
                          "rendererId": "bokeh",
                          "legend": "false"
                        }
                    </pd_options>
                </button>
                <br/>
                <button pd_entity="homes" pd_target="target{{prefix}}" type="button">
                    Map
                    <pd_options>
                        {
                          "coloropacity": "65",
                          "kind": "densitymap",
                          "keyFields": "LATITUDE,LONGITUDE",
                          "rendererId": "mapbox",
                          "aggregation": "AVG",
                          "rowCount": "500",
                          "handlerId": "mapView",
                          "valueFields": "PRICE",
                          "mapboxtoken": "pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4M29iazA2Z2gycXA4N2pmbDZmangifQ.-g_vE53SD2WrJ6tFX7QHmA"
                        }
                    </pd_options>
                </button>
                
            </div>
            <div class="col-sm-10" id="target{{prefix}}"/>
        </div>
        """)
        managed_client = ManagedClientPool.instance().get()
        with (yield managed_client.lock.acquire()):
            try:
                response = yield managed_client.execute_code(code, self.result_extractor)
                self.render("template/main.html", response = response)
            except:
                traceback.print_exc()

    def result_extractor(self, result_accumulator):
        res = []
        for msg in result_accumulator:
            if msg['header']['msg_type'] == 'stream':
                res.append(msg['content']['text'])
            elif msg['header']['msg_type'] == 'display_data':
                if "data" in msg['content'] and "text/html" in msg['content']['data']:
                    res.append(msg['content']['data']['text/html'])
                else:
                    print("display_data msg not processed: {}".format(msg))                    
            elif msg['header']['msg_type'] == 'error':
                error_name = msg['content']['ename']
                error_value = msg['content']['evalue']
                return 'Error {}: {} \n'.format(error_name, error_value)
            else:
                print("Message type not processed: {}".format(msg))
        return ''.join(res)

class PixieAppHandler(TestHandler):
    @gen.coroutine
    def get(self, *args, **kwargs):
        clazz = args[0]

        #check the notebooks first
        pixieapp_def = NotebookMgr.instance().get_notebook_pixieapp(clazz)
        code = None
        managed_client = ManagedClientPool.instance().get()
        if pixieapp_def is not None:
            yield pixieapp_def.warmup(managed_client)
            code = pixieapp_def.get_run_code(self.session)
        else:
            instance_name = self.session.getInstanceName(clazz)
            code = """
def my_import(name):
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod
clazz = "{clazz}"

{instance_name} = my_import(clazz)()
{instance_name}.run()
            """.format(clazz=args[0], instance_name=instance_name)

        with (yield managed_client.lock.acquire()):
            try:
                response = yield managed_client.execute_code(code, self.result_extractor)
                self.render("template/main.html", response = response, title=pixieapp_def.title if pixieapp_def is not None else None)
            except:
                traceback.print_exc()

class PixieDustHandler(tornado.web.RequestHandler):
    def initialize(self, loadjs):
        self.loadjs = loadjs

    def get(self):
        from pixiedust.display.display import Display
        class PixieDustDisplay(Display):
            def doRender(self, handlerId):
                pass
        self.set_header('Content-Type', 'text/javascript' if self.loadjs else 'text/css')
        disp = PixieDustDisplay({"gateway":"true"}, None)
        disp.callerText = "display(None)"
        self.write(disp.renderTemplate("pixiedust.js" if self.loadjs else "pixiedust.css"))
        self.finish()

class PixieAppListHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("template/pixieappList.html", pixieapp_list=NotebookMgr.instance().notebook_pixieapps())

class PixieAppPublish(tornado.web.RequestHandler):
    @gen.coroutine
    def post(self, name):
        payload = self.request.body.decode('utf-8')
        try:
            notebook = nbformat.from_dict(json.loads(payload))
            pixieapp_model = yield NotebookMgr.instance().publish(name, notebook)
            self.set_status(200)
            self.write(json.dumps(pixieapp_model))
            self.finish()
        except Exception as exc:
            print(traceback.print_exc())
            raise web.HTTPError(400, u'Publish PixieApp error: {}'.format(exc))

class PixieDustLogHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        self.set_header('Content-Type', 'text/html')
        self.set_status(200)
        code = """
import pixiedust
%pixiedustLog -l debug
        """
        managed_client = ManagedClientPool.instance().get()
        with (yield managed_client.lock.acquire()):
            try:
                response = yield managed_client.execute_code(code, self.result_extractor)
                self.write(response)
            except:
                traceback.print_exc()
            finally:
                self.finish()

    def result_extractor(self, result_accumulator):
        res = []
        for msg in result_accumulator:
            if msg['header']['msg_type'] == 'stream':
                res.append( msg['content']['text'])
            elif msg['header']['msg_type'] == 'display_data':
                if "data" in msg['content'] and "text/html" in msg['content']['data']:
                    res.append( msg['content']['data']['text/html'] )                    
            elif msg['header']['msg_type'] == 'error':
                error_name = msg['content']['ename']
                error_value = msg['content']['evalue']
                return 'Error {}: {} \n'.format(error_name, error_value)

        return '<br/>'.join([w.replace('\n', '<br/>') for w in res])