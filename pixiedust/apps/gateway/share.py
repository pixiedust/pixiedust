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
from pixiedust.display.app import *
from pixiedust.apps.gateway import BaseGatewayApp
from pixiedust.utils.shellAccess import ShellAccess
from pixiedust.utils.userPreferences import setUserPreference
from IPython.utils.io import capture_output
import requests

@PixieApp
class ShareChartApp(BaseGatewayApp):
    def setup(self):
        BaseGatewayApp.setup(self)
        self.title = "Share Chart and make it accessible on the web"
        self.tab_definitions = [{
            "title": "Basic Shared Options",
            "id": "options",
            "name": "Options",
            "contents": lambda: self.renderTemplate("shareBasicOptions.html")
        }
        # ,{
        #     "title": "Access Control",
        #     "id": "permissions",
        #     "name": "Permissions",
        #     "contents": lambda: self.renderTemplate("sharePermissionsOptions.html")
        # },{
        #     "title": "Chart Refresh Options",
        #     "id": "refresh",
        #     "name": "Refresh",
        #     "contents": lambda: self.renderTemplate("shareRefreshOptions.html")
        # }
        ]
        self.gateway_buttons = [{
            "title": "Share",
            "options": ["server", "description"]
        }]

    def update_command(self, command, key, value):
        has_value = value is not None and value != ''
        pattern = ("" if has_value else ",")+"\\s*" + key + "\\s*=\\s*'((\\\\'|[^'])*)'"
        m = re.search(pattern, str(command), re.IGNORECASE)
        ret_command = command
        if m is not None:
            ret_command = command.replace(m.group(0), key+"='"+value+"'" if has_value else "")
        elif has_value:
            k = command.rfind(")")
            ret_command = command[:k]
            ret_command += ","+key+"='"+value+"'"
            ret_command += command[k:]
        return ret_command

    @route(gateway_server="*")
    def shareIt(self, gateway_server, gateway_description):
        self.server = gateway_server
        setUserPreference("pixie_gateway_server", gateway_server)
        with capture_output() as buf:
            try:
                command = self.parent_command
                #add any options from the current cell metadata
                if self.cell_metadata is not None and 'pixiedust' in self.cell_metadata and 'displayParams' in self.cell_metadata['pixiedust']:
                    for key,value in iteritems(self.cell_metadata['pixiedust']['displayParams']):
                        command = self.update_command(command, key, value)
                command = self.update_command(command, "nostore_figureOnly", "true")
                sys.modules['pixiedust.display'].pixiedust_display_callerText = command
                for key in ShellAccess:
                    locals()[key] = ShellAccess[key]
                eval(command, globals(), locals())
            finally:
                del sys.modules['pixiedust.display'].pixiedust_display_callerText

        payload = {
            "chart": "\n".join([output._repr_html_() for output in buf.outputs]),
            "description": gateway_description
        }
        #return print("<pre>{}</pre>".format(payload))
        
        response = requests.post(
            "{}/chart".format(self.server), 
            json = payload
        )
        if response.status_code == requests.codes.ok:
            self.chart_model = response.json()
            return """
<style type="text/css">
.share{
    font-size: larger;
    margin-left: 30px;
}
.publish .summary{
    font-size: xx-large;
    text-align: center;
}
</style>
<div class="share">
    <div class="summary">
        <div>Chart Successfully shared</div>
        <div>
            <a href="{{this.server}}/chart/{{this.chart_model['CHARTID']}}" target="blank">
                {{this.server}}/chart/{{this.chart_model['CHARTID']}}
            </a>
        </div>
    </div>
</div>
            """
        
        return "<div>An Error occured while sharing this chart: {}".format(response.text)
        #print(payload)

    @route()
    def main(self):
        return self._addHTMLTemplate("mainOptions.html")