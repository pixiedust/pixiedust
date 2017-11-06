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
import os
from traitlets.config.configurable import LoggingConfigurable
import tornado
from tornado.concurrent import Future
from tornado import gen, locks
from tornado.log import app_log
from .pixieGatewayApp import PixieGatewayApp
from .managedClient import ManagedClient, ManagedClientPool
from .session import SessionManager
from .notebookMgr import NotebookMgr
from .handlers import (
    PixieDustHandler, PixieDustLogHandler, ExecuteCodeHandler, PixieAppHandler,
    PixieAppListHandler, PixieAppPublishHandler, ChartShareHandler, StatsHandler,
    AdminHandler, ChartEmbedHandler
)

def main():
    os.environ['PIXIEDUST_DB_NAME'] = "gateway.db"
    PixieGatewayApp.launch_instance()

class PixieGatewayTemplatePersonality(LoggingConfigurable):
    def init_configurables(self):
        for spec in self.parent.kernel_manager.kernel_spec_manager.get_all_specs():
            app_log.info(spec)
        self.managed_client_pool = ManagedClientPool.instance(self.parent.kernel_manager)
        self.notebook_mgr = NotebookMgr()

    def shutdown(self):
        """During a proper shutdown of the kernel gateway, this will be called so that
        any held resources may be properly released."""
        self.managed_client_pool.shutdown()
        SessionManager.instance().shutdown()

    def create_request_handlers(self):
        """Returns a list of zero or more tuples of handler path, Tornado handler class
        name, and handler arguments, that should be registered in the kernel gateway's
        web application. Paths are used as given and should respect the kernel gateway's
        `base_url` traitlet value."""
        pixiedust_home = os.environ.get("PIXIEDUST_HOME", os.path.expanduser('~'))
        return [
            (r"/static/(.*)", tornado.web.StaticFileHandler, {'path': os.path.join( pixiedust_home, 'static')}),
            (r"/pixiedustLog", PixieDustLogHandler),
            (r"/pixiedust.js", PixieDustHandler, {'loadjs':True}),
            (r"/pixiedust.css", PixieDustHandler, {'loadjs':False}),
            (r"/executeCode/(.*)", ExecuteCodeHandler),
            (r"/pixieapp/(.*)", PixieAppHandler),
            (r"/admin(?:/(?P<tab_id>(?:.*))?)?", AdminHandler),
            (r"/pixieapps", PixieAppListHandler),
            (r"/publish/(?P<name>(?:.*))", PixieAppPublishHandler),
            (r"/chart(?:/(?P<chart_id>(?:.*))?)?", ChartShareHandler),
            (r"/embed(?:/(?P<chart_id>[^/]*)(?:/(?P<width>\d+))?(?:/(?P<height>\d+))?)?", ChartEmbedHandler),
            (r"/stats(?:/(?P<command>(?:.*))?)?", StatsHandler, {"km":self.parent.kernel_manager})
        ]

    def should_seed_cell(self, code):
        """Determines whether the kernel gateway will include the given notebook code
        cell when seeding a new kernel. Will only be called if a seed notebook has
        been specified."""
        pass

def create_personality(*args, **kwargs):
    return PixieGatewayTemplatePersonality(*args, **kwargs)