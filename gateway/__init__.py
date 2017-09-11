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
from traitlets.config.configurable import LoggingConfigurable
import tornado
from tornado.concurrent import Future
from tornado import gen, locks
from .pixieGatewayApp import PixieGatewayApp
from .managedClient import ManagedClient
from .handlers import PixieDustHandler, PixieDustLogHandler, ExecuteCodeHandler, DynArgsHandler, TestHandler

def main():
    PixieGatewayApp.launch_instance()

class PixieGatewayTemplatePersonality(LoggingConfigurable):
    def init_configurables(self):
        for spec in self.parent.kernel_manager.kernel_spec_manager.get_all_specs():
            print(spec)

        self.managed_client = ManagedClient(self.parent.kernel_manager)

    def shutdown(self):
        """During a proper shutdown of the kernel gateway, this will be called so that
        any held resources may be properly released."""
        pass 

    def create_request_handlers(self):
        """Returns a list of zero or more tuples of handler path, Tornado handler class
        name, and handler arguments, that should be registered in the kernel gateway's
        web application. Paths are used as given and should respect the kernel gateway's
        `base_url` traitlet value."""
        return [
            ("/pixiedustLog", PixieDustLogHandler, {'managed_client': self.managed_client}),
            ("/myapp", TestHandler, {'managed_client': self.managed_client}),
            ("/pixiedust.js", PixieDustHandler, {'loadjs':True}),
            ("/pixiedust.css", PixieDustHandler, {'loadjs':False}),
            ("/executeCode", ExecuteCodeHandler, {'managed_client': self.managed_client}),
            ("/pixieapp/(.*)", DynArgsHandler, {'managed_client': self.managed_client})
        ]

    def should_seed_cell(self, code):
        """Determines whether the kernel gateway will include the given notebook code
        cell when seeding a new kernel. Will only be called if a seed notebook has
        been specified."""
        pass

def create_personality(*args, **kwargs):
    return PixieGatewayTemplatePersonality(*args, **kwargs)