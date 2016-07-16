# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2016
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
from jinja2 import BaseLoader, Environment
import pkg_resources
import inspect
import sys

class PixiedustTemplateLoader(BaseLoader):
    def __init__(self, baseModule, path="templates"):
        self.path=path
        self.baseModule = baseModule

    def get_source(self, environment, template):
        parts = template.split(":")
        module=None
        templatePath=None
        if len(parts) == 1:
            module=self.baseModule
            templatePath=parts[0]
        elif len(parts) == 2:
            module=parts[0]
            templatePath=parts[1]
        else:
            raise TemplateError("Invalid syntax " + template )
        
        if module=="__main__":
            module=self.baseModule

        path = self.path + "/" + templatePath
        return pkg_resources.resource_string(module,path).decode('utf-8'), templatePath, lambda: False

class PixiedustTemplateEnvironment(object):
    
    def __init__(self, baseModule=None):
        if not baseModule:
            frm = inspect.stack()[1]
            baseModule = inspect.getmodule(frm[0]).__name__
        self.env = Environment(loader=PixiedustTemplateLoader(baseModule))
    
    def getTemplate(self, name):
        visited = {}
        for frm in inspect.stack():
            mod = inspect.getmodule(frm[0])
            if mod and mod.__name__ not in visited:
                try:
                    visited[mod.__name__]=mod
                    return self.env.get_template( mod.__name__ + ":" + name )
                except:
                    pass
        
        #if we are here, we didn't find it
        raise
    