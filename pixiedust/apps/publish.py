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

import json
import requests
from pixiedust.display.app import *

@PixieApp
class PublishApp():
    """
    Publish a PixieApp as a web app
    """
    def process(self, content):
        content = json.loads(content)
        response = requests.post(
            "http://localhost:8899/publish/{}".format(content['name']), 
            json = content['notebook']
        )
        print("<div>nb{}</div>".format(response.text))
        
    @route()
    def main(self):
        return """
<script>
function getNotebookJSON(){
    return {
        "name": IPython.notebook.notebook_name,
        "notebook": IPython.notebook.toJSON()
    }
}
</script>
<button type="button" pd_target="nb{{prefix}}">
    Publish
    <pd_script>
self.process('''$val(getNotebookJSON)''')
    </pd_script>
</button>
<div id="nb{{prefix}}"></div>
        """