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
import nbformat
import tornado
from tornado import gen, web
from tornado.log import app_log
from six import PY3, iteritems
from .session import SessionManager
from .notebookMgr import NotebookMgr
from .managedClient import ManagedClientPool
from .chartsManager import chart_storage
from .utils import sanitize_traceback

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        pass

    def prepare(self):
        """
        Retrieve session for current user
        """
        self.session = SessionManager.instance().get_session(self)
        app_log.debug("session %s", self.session)

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
    def post(self, *args, **kwargs):
        run_id = args[0]
        managed_client = self.session.get_managed_client_by_run_id(run_id)
        with (yield managed_client.lock.acquire()):
            try:
                response = yield managed_client.execute_code(self.request.body.decode('utf-8'))
                self.write(response)
            except:
                traceback.print_exc()
            finally:
                self.finish()

class PixieAppHandler(BaseHandler):
    """
    Entry point for running a PixieApp
    """
    def handle_exception(self, exc):
        self.write("<div>Code Execution error <pre>{}</pre></div>".format(exc))
        self.write("<pre>")
        for line in traceback.format_stack():
            self.write(line)
        self.write("</pre>")
        #raise web.HTTPError(500, u'Execution error: {}'.format(exc))
        self.finish()

    @gen.coroutine
    def get(self, *args, **kwargs):
        clazz = args[0]

        #check the notebooks first
        pixieapp_def = NotebookMgr.instance().get_notebook_pixieapp(clazz)
        code = None
        managed_client = self.session.get_managed_client(self, pixieapp_def, True)
        if pixieapp_def is not None:
            try:
                yield pixieapp_def.warmup(managed_client)
                code = pixieapp_def.get_run_code(self.session, self.session.get_pixieapp_run_id(self, pixieapp_def))
            except Exception as exc:
                self.handle_exception(exc)
                return
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
            except Exception as exc:
                self.handle_exception(exc)

    def result_extractor(self, result_accumulator):
        res = []
        for msg in result_accumulator:
            if msg['header']['msg_type'] == 'stream':
                res.append(msg['content']['text'])
            elif msg['header']['msg_type'] == 'display_data':
                if "data" in msg['content'] and "text/html" in msg['content']['data']:
                    res.append(msg['content']['data']['text/html'])
                else:
                    app_log.warning("display_data msg not processed: %s", msg)                    
            elif msg['header']['msg_type'] == 'error':
                error_name = msg['content']['ename']
                error_value = msg['content']['evalue']
                trace = sanitize_traceback(msg['content']['traceback'])
                return 'Error {}: {}\n{}\n'.format(error_name, error_value, trace)
            else:
                app_log.warning("Message type not processed: %s", msg['header']['msg_type'])
        return ''.join(res)

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

class PixieAppPublishHandler(tornado.web.RequestHandler):
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

class ChartShareHandler(tornado.web.RequestHandler):
    def post(self, chart_id):
        payload = json.loads(self.request.body.decode('utf-8'))
        try:
            chart_model = chart_storage.store_chart(payload)
            self.set_status(200)
            self.write(json.dumps(chart_model))
            self.finish()
        except Exception as exc:
            print(traceback.print_exc())
            raise web.HTTPError(400, u'Share Chart error: {}'.format(exc))

    def get(self, chart_id):
        chart_model = chart_storage.get_chart(chart_id)
        if chart_model is not None:
            self.render("template/showChart.html", chart_model=chart_model)
        else:
            self.set_status(404)
            self.write("Chart not found")

class StatsHandler(tornado.web.RequestHandler):
    """
    Provides various stats about the running kernels
    """
    def initialize(self, km):
        self.kernel_manager = km

    def get(self, command):
        if command is None:
            self.write(ManagedClientPool.instance().get_stats())
        elif command == "kernels":
            specs = self.kernel_manager.kernel_spec_manager.get_all_specs()
            for k, v in iteritems(specs):
                v['default'] = True if k == ('python3' if PY3 else 'python2') else False
            self.write(specs)
        else:
            raise web.HTTPError(400, u'Unknown stat command: {}'.format(command))

class PixieDustLogHandler(BaseHandler):
    """
    Access the PixieDust Logs
    """
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
                trace = sanitize_traceback(msg['content']['traceback'])
                return 'Error {}: {}\n{}\n'.format(error_name, error_value, trace)

        return '<br/>'.join([w.replace('\n', '<br/>') for w in res])