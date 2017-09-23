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
from pixiedust.utils.userPreferences import getUserPreference, setUserPreference
import requests
import nbformat

import ast
class ImportsLookup(ast.NodeVisitor):
    def __init__(self):
        self.imports=set()
    
    #pylint: disable=E0213,E1102
    def onvisit(func):
        def wrap(self, node):
            ret_node = func(self, node)
            super(ImportsLookup, self).generic_visit(node)
            return ret_node
        return wrap
    
    @onvisit
    def visit_ImportFrom(self, node):
        self.imports.add(node.module.split(".")[0])
    
    @onvisit
    def visit_Import(self, node):
        for name in node.names:
            self.imports.add(name.name)
        
    @onvisit
    def generic_visit(self, node):
        pass

@PixieApp
class PublishApp():
    """
    Publish a PixieApp as a web app
    """
    
    def setup(self):
        self.server = getUserPreference("pixie_gateway_server", "http://localhost:8899")
    
    @route(publish="*")
    def publish(self, publish):
        self.server = publish
        setUserPreference("pixie_gateway_server", publish)
        response = requests.post(
            "{}/publish/{}".format(self.server, self.contents['name']), 
            json = self.contents['notebook']
        )
        if response.status_code == requests.codes.ok:
            return "<div>Notebook Successfully published</div>"
        
        return "<div>An Error occured while publishing this notebook: {}".format(response.text)
        
    @route(importTable="*")
    def imports(self):
        notebook = nbformat.from_dict(self.contents['notebook'])
        code = ""
        for cell in notebook.cells:
            if cell.cell_type == "code":
                code += "\n" + cell.source                
        self.lookup = ImportsLookup()
        self.lookup.visit(ast.parse(code))
        return """
<table class="table">
    <thead>
        <tr>
            <th>Import</th>
            <th>Package</th>
        </tr>
    </thead>
    <tbody>
        {% for import in this.lookup.imports%}
        <tr>
            <td>{{import}}</td>
            <td>{{import}}</td>
        </tr>
        {%endfor%}
    </tbody>
</table>
        """
    
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
<div class="container col-sm-12">
    <div class="row">
        <div class="form-group col-sm-12" style="padding-right:10px;">
            <label for="server{{prefix}}">PixieGateway Server:</label>
            <input type="text" class="form-control" id="server{{prefix}}" name="server" value="{{this.server}}">
        </div>
    </div>
    <div class="row">
        <div class="form-group col-sm-12" style="padding-right:10px;">
            <label for="imports{{prefix}}">Imports:</label>
            <div pd_render_onload pd_refresh pd_options="importTable=true">
                <pd_script>
self.contents = json.loads('''$val(getNotebookJSON)''')
                </pd_script>
            </div>
        </div>
    </div>
</div>
<center><button type="button" class="btn btn-primary" pd_options="publish=$val(server{{prefix}})">
    Publish
</button></center>
<div id="nb{{prefix}}"></div>
        """