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
from traitlets.config.application import Application
from jupyter_client.kernelspecapp  import ListKernelSpecs
from traitlets import Unicode, Dict
from .createKernel import PixiedustInstall
from .generate import PixiedustGenerate

class PixiedustList(ListKernelSpecs):
    pass

class PixiedustJupyterApp(Application):
    subcommands = Dict({
        'install': (PixiedustInstall, "Install Kernels locally for development with Pixiedust"),
        'list': (PixiedustList, "List of pixiedust kernels"),
        'generate': (PixiedustGenerate, "Generate boiler plate code for a PixieDust plugin")
    })
    def start(self):
        if self.subapp is None:
            print('Invalid syntax: You need to specify a subcommand from this list {0}'.format(list(self.subcommands)))
            print()
            self.print_subcommands()
            self.exit(1)
        else:
            return self.subapp.start()

def main():
    PixiedustJupyterApp.launch_instance()