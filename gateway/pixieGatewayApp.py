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
import base64
import uuid
from kernel_gateway.gatewayapp import KernelGatewayApp
from traitlets import Unicode, default

class PixieGatewayApp(KernelGatewayApp):
    def initialize(self, argv=None):
        self.api = 'gateway'
        #self.api = 'notebook-http'
        super(PixieGatewayApp, self).initialize(argv)

    def init_webapp(self):
        super(PixieGatewayApp, self).init_webapp()
        self.web_app.settings["cookie_secret"] = base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes).decode("UTF-8")

    prepend_execute_code = Unicode(None, config=True, allow_none=True,help="""Code to prepend before each execution""")

    @default('prepend_execute_code')
    def prepend_execute_code_default(self):
        return ""