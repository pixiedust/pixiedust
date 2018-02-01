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
from pixiedust.utils.userPreferences import getUserPreference, setUserPreference, user_preferences
from pixiedust.utils import Logger
from pixiedust.apps.gateway import BaseGatewayApp
import warnings
import pkg_resources
from jupyter_client.manager import KernelManager
from IPython.core.getipython import get_ipython

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
            try:
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
                        pkg = pkg_resources.get_distribution(module_name)
                        version = pkg.parsed_version._version.release
                        self.imports.add( (module_name, version, self.get_egg_url(pkg, module_name)) )
                    except pkg_resources.DistributionNotFound:
                        pass
            except:
                print("Unknown import found {}".format(module_name))

    def get_egg_url(self, pkg, module_name):
        if requests.get("https://pypi.python.org/pypi/{}/json".format(module_name), timeout=5).status_code == 200:
            return None
        def try_location(base, name):
            ret = os.path.join(base,name)
            if not os.path.exists(ret):
                ret = os.path.join(base, name.replace("-", "_"))
            if not os.path.exists(ret):
                ret = os.path.join(base, name.replace("_", "-"))
            return ret
        
        location = pkg.location
        if not os.path.exists(os.path.join(location, "setup.py")):
            location = try_location(location, module_name)
        if not os.path.exists(os.path.join(location, "setup.py")):
            #try the github page
                pkg_info = os.path.join(pkg.location, "{}.egg-info".format(pkg.egg_name()), "PKG-INFO")
                if os.path.isfile(pkg_info):
                    with open(pkg_info) as fp:
                        for line in fp.readlines():
                            index = line.find(':')
                            if index>0:
                                key = line[0:index].strip()
                                if key.lower()=="home-page":
                                    return "git+{}#egg={}".format(line[index+1:].strip(), module_name)
    
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
@user_preferences(security='token')
class PublishApp(BaseGatewayApp):
    """
    Publish a PixieApp as a web app
    """
    
    def setup(self):
        BaseGatewayApp.setup(self)
        self.kernel_spec = None
        self.kernel_name = None
        self.kernels = []
        self.lookup = None
        self.title = "Publish PixieApp to the web"
        self.tab_definitions = [{
            "title": "Basic Publish Options",
            "id": "options",
            "name": "Options",
            "contents": lambda: self.renderTemplate("publishBasicOptions.html")
        }, {
            "title": "Security",
            "id": "security",
            "name": "Security",
            "contents": lambda: self.renderTemplate("publishSecurityOptions.html")
        }, {
            "title": "Package dependencies",
            "id": "imports",
            "name": "Imports",
            "contents": lambda: self.renderTemplate("publishImportOptions.html")
        }, {
            "title": "Kernel Specification",
            "id": "kernelspec",
            "name": "Kernel Spec",
            "contents": lambda: self.renderTemplate("publishKernelSpecOptions.html")
        }]
        self.gateway_buttons = [{
            "title": "Publish",
            "options": ["server", "title", "icon", "sel_kernel"]
        }]
        self.set_gateway_server()

    def set_gateway_server(self, gateway_server = None):
        server = gateway_server.strip("/ ") if gateway_server is not None else self.server.strip("/ ")
        message = ""
        icon = "fa-check"
        try:
            #get the list of kernels
            response = requests.get("{}/stats/kernels".format(server), timeout=5)
            if response.status_code != requests.codes.ok:
                raise Exception(response.text)
            kernels_spec = response.json()
            if self.kernel_name and self.kernel_name in kernels_spec:
                for spec in kernels_spec.values(): spec['default'] = False
                kernels_spec[self.kernel_name]['default'] = True
            self.kernels = [(kernel, spec['default']) for kernel,spec in iteritems(kernels_spec)]

            message = "PixieGateway successfully validated. You can optionally pick a kernel in the Kernels tab"
        except Exception as exc:
            icon="fa-times"
            message = str(exc)
            self.error( "Unable to validate gateway server {} - {}".format(server, exc))


        if gateway_server is not None:
            print("""
                    <span style="bottom:0px;position:absolute">
                        <i style="font-size:2em" class="fa {}" aria-hidden="true"></i>
                        <span>{}</span>
                    </span>
                """.format(icon, message))

    def set_contents(self, contents):
        self.contents = json.loads(contents)
        self.contents['notebook']['metadata']['pixiedust'] = {}
        kernel_spec = self.contents['notebook']['metadata']['kernelspec']
        self.kernel_name=kernel_spec['name']
        km = KernelManager(kernel_name=kernel_spec['name'])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.kernel_spec = json.dumps(km.kernel_spec.to_dict(), indent=4, sort_keys=True)

    @route(gateway_server="*")
    def publish(self, gateway_server, gateway_title, gateway_icon, gateway_sel_kernel):
        self.server = gateway_server.strip("/ ")
        self.contents['notebook']['metadata']['pixiedust'].update({
            "title":gateway_title, "icon":gateway_icon, "security": self.security
        })
        if gateway_sel_kernel != "Default":
            self.contents['notebook']['metadata']['pixiedust'].update({"kernel":gateway_sel_kernel})
        self.compute_imports()
        setUserPreference("pixie_gateway_server", gateway_server)
        response = requests.post(
            "{}/publish/{}".format(self.server, self.contents['name']), 
            json = self.contents['notebook']
        )
        if response.status_code == requests.codes.ok:
            self.pixieapp_model = response.json()
            return """
<style type="text/css">
.publish{
    font-size: larger;
    margin-left: 30px;
}
.publish .logmessages{
}
.publish .logmessage{
    color: darkblue;
}
.publish .summary{
    font-size: xx-large;
    text-align: center;
}
</style>
<div class="publish">
    <div class="logmessages">
        {%for message in this.pixieapp_model['log']%}
        <div class="logmessage">
            {{message}}
        </div>
        {%endfor%}
    </div>
    <div class="summary">
        <div>Notebook Successfully published</div>
        <div>
            <a href="{{this.pixieapp_model['url']}}" target="blank">
                {{this.contents['name']}}
            </a>
        </div>
    </div>
</div>
            """
        
        return "<div>An Error occured while publishing this notebook: {}".format(response.text)

    
    def ast_parse(self, code):
        try:
            return ast.parse(code)
        except SyntaxError:
            #transform the code first to handle notebook syntactic sugar like magic and system
            return ast.parse(
                get_ipython().input_transformer_manager.transform_cell(code)
            )

    def compute_imports(self):
        if self.lookup is None:
            notebook = nbformat.from_dict(self.contents['notebook'])
            code = ""
            for cell in notebook.cells:
                if cell.cell_type == "code":
                    code += "\n" + cell.source                
            self.lookup = ImportsLookup()
            self.lookup.visit(ast.parse(self.ast_parse(code)))
            self.contents['notebook']['metadata']['pixiedust'].update({
                "imports": {p[0]:{"version":p[1],"install":p[2]} for p in self.lookup.imports}
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
            <th>Install</th>
        </tr>
    </thead>
    <tbody>
        {% for import in this.lookup.imports%}
        <tr>
            <td>{{import[0]}}</td>
            <td>{{import[1]}}</td>
            <td>{{import[2] or "PyPi"}}</td>
        </tr>
        {%endfor%}
    </tbody>
</table>
        """
    
    @route(showKernelSpec="*")
    def show_kernel_spec(self):
        return "<pre>{{this.kernel_spec}}</pre>"
