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
import sys
import os
import requests
import json
import nbformat
from pixiedust.utils.userPreferences import getUserPreference, setUserPreference
from pixiedust.utils import Logger
import warnings
import pkg_resources
from jupyter_client.manager import KernelManager

import ast
class ImportsLookup(ast.NodeVisitor):
    def __init__(self):
        self.imports = set()

    #pylint: disable=E0213,E1102
    def onvisit(func):
        def wrap(self, node):
            ret_node = func(self, node)
            super(ImportsLookup, self).generic_visit(node)
            return ret_node
        return wrap

    def add_import(self, module_name):
        if not module_name in sys.builtin_module_names:
            module = __import__(module_name)
            ok_to_add = module.__package__ != ""
            if not ok_to_add and "site-packages" in module.__file__:
                ok_to_add = True
            #check if egg-link (aka editable mode)
            if not ok_to_add:
                for p in sys.path:
                    if os.path.isfile(os.path.join(p,module_name+".egg-link")):
                        ok_to_add = True

            if ok_to_add:
                try:
                    version = pkg_resources.get_distribution(module_name).parsed_version._version.release
                    self.imports.add( (module_name, version) )
                except pkg_resources.DistributionNotFound:
                    pass
    
    @onvisit
    def visit_ImportFrom(self, node):
        self.add_import(node.module.split(".")[0])
    
    @onvisit
    def visit_Import(self, node):
        for name in node.names:
            self.add_import(name.name)
        
    @onvisit
    def generic_visit(self, node):
        pass

@PixieApp
@Logger()
class PublishApp():
    """
    Publish a PixieApp as a web app
    """
    
    def setup(self):
        self.server = getUserPreference("pixie_gateway_server", "http://localhost:8899")
        self.kernel_spec = None
        self.lookup = None
        
    def set_contents(self, contents):
        self.contents = json.loads(contents)
        self.contents['notebook']['metadata']['pixiedust'] = {}
        kernel_spec = self.contents['notebook']['metadata']['kernelspec']
        km = KernelManager(kernel_name=kernel_spec['name'])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.kernel_spec = json.dumps(km.kernel_spec.to_dict(), indent=4, sort_keys=True)
    
    @route(publish_server="*")
    def publish(self, publish_server, publish_title, publish_icon):
        self.debug("server david {}".format(publish_server))
        self.server = publish_server
        self.contents['notebook']['metadata']['pixiedust'].update({"title":publish_title, "icon":publish_icon})
        self.compute_imports()
        setUserPreference("pixie_gateway_server", publish_server)
        response = requests.post(
            "{}/publish/{}".format(self.server, self.contents['name']), 
            json = self.contents['notebook']
        )
        if response.status_code == requests.codes.ok:
            self.pixieapp_model = response.json()
            return """
            <div>Notebook Successfully published</div>
            <a href="{{this.server}}/pixieapp/{{this.pixieapp_model['name']}}" target="blank">
                {{this.contents['name']}}
            </a>
            """
        
        return "<div>An Error occured while publishing this notebook: {}".format(response.text)

    def _sanitizeCode(self, code):
        def translateMagicLine(line):
            index = line.find('%')
            if index >= 0:
                try:
                    ast.parse(line)
                except SyntaxError:
                    magic_line = line[index+1:].split()
                    line= """{} get_ipython().run_line_magic("{}", "{}")""".format(
                        line[:index], magic_line[0], ' '.join(magic_line[1:])
                        ).strip()
            return line
        return '\n'.join([translateMagicLine(p) for p in code.split('\n') if not p.strip().startswith('!')])

    def compute_imports(self):
        if self.lookup is None:
            notebook = nbformat.from_dict(self.contents['notebook'])
            code = ""
            for cell in notebook.cells:
                if cell.cell_type == "code":
                    code += "\n" + cell.source                
            self.lookup = ImportsLookup()
            self.lookup.visit(ast.parse(self._sanitizeCode(code)))
            self.contents['notebook']['metadata']['pixiedust'].update({
                "imports": {p[0]:p[1] for p in self.lookup.imports}
            })
        
    @route(importTable="*")
    def imports(self):
        self.compute_imports()
        return """
<table class="table">
    <thead>
        <tr>
            <th>Package</th>
            <th>Version</th>
        </tr>
    </thead>
    <tbody>
        {% for import in this.lookup.imports%}
        <tr>
            <td>{{import[0]}}</td>
            <td>{{import[1]}}</td>
        </tr>
        {%endfor%}
    </tbody>
</table>
        """
    
    @route(showKernelSpec="*")
    def show_kernel_spec(self):
        return "<pre>{{this.kernel_spec}}</pre>"
    
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

$(".publishOptions .nav a").on("click", function(){
   n = $(".publishOptions .nav").find(".active");
   o = $(".publishContents").find(".collapse.in");
   p = $(this).parent();
   if (n[0] != p[0]){
       n.removeClass("active");
       o.removeClass("in")
       p.addClass("active");
    }
});
</script>

<style type="text/css">
.publishOptions{
    background-color: #fff;
    border: 1px solid #d1d5da;
    border-radius: 3px;
}
.publishOptions a{
    text-decoration:none !important;
}

.publishOptions li:not(.active) a{
    text-decoration:none !important;
    color: initial !important;
}
.publishOptions ul{
    padding-left: 0px !important;
}

.publishOptions2 .nav-pills>li.active>a, .publishOptions .nav-pills>li.active>a:focus, .publishOptions.nav-pills>li.active>a:hover {
    color: #fff;
    background-color: #337ab7;
}
.publishContents{
    padding-left:10px;
    min-height:200px;
}
</style>
<div style="display: flex;
    padding-bottom: 8px;
    margin-bottom: 16px;
    border-bottom: 1px #e1e4e8 solid;
    flex-flow: row wrap;">
    <h2>Publish Notebook as a web application</h2>
</div>
<div class="container" style="width:inherit">
    <div class="row">
        <div class="col-sm-2 publishOptions">
            <div>
                <ul class="nav nav-pills nav-stacked">
                   <li class="active"><a data-toggle="collapse" data-target="#options{{prefix}}" href="#">Options</a></li>
                   <li><a data-toggle="collapse" data-target="#imports{{prefix}}" href="#">Imports</a></li>
                   <li><a data-toggle="collapse" data-target="#kernelspec{{prefix}}" href="#">Kernel Spec</a></li>
                </ul>
            </div>
        </div>
        <div class="col-sm-10 publishContents">
            <div id="options{{prefix}}" class="collapse in">
                <div class="form-group">
                    <label for="server{{prefix}}">PixieGateway Server:</label>
                    <input type="text" class="form-control" id="server{{prefix}}" name="server" value="{{this.server}}">
                </div>
                <div class="form-group">
                    <label for="title{{prefix}}">Page Title:</label>
                    <input type="text" class="form-control" id="title{{prefix}}" name="title" value="">
                </div>
                <div class="form-group">
                    <label for="icon{{prefix}}">Page Icon:</label>
                    <input type="text" class="form-control" id="icon{{prefix}}" name="icon" value="">
                </div>
                <div>
                    <input type="checkbox" id="run{{prefix}}" name="run" value="1">
                    <label for="run{{prefix}}">Run application in dedicated kernel</label>
                </div>
            </div>
            <div id="imports{{prefix}}" class="collapse">
                <div class="form-group">
                    <label for="imports{{prefix}}">List of packages that will be automaticall imported if needed:</label>
                    <div pd_render_onload pd_refresh pd_options="importTable=true">
                        <pd_script>
self.set_contents('''$val(getNotebookJSON)''')
                        </pd_script>
                    </div>
                </div>
            </div>
            <div id="kernelspec{{prefix}}" class="collapse">
                <div pd_render_onload pd_refresh pd_options="showKernelSpec=true">
                </div>
            </div>
        </div>
    </div>
</div>

<center>
    <button type="button" class="btn btn-primary">
        <pd_options>
        {
            "publish_server": "$val(server{{prefix}})",
            "publish_title":"$val(title{{prefix}})",
            "publish_icon":"$val(icon{{prefix}})"
        }
        </pd_options>
    Publish
    </button>
</center>
<div id="nb{{prefix}}"></div>
        """
