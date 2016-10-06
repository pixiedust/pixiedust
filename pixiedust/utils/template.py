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
from jinja2 import BaseLoader, Environment, TemplateSyntaxError, TemplateAssertionError, TemplateError
import pkg_resources
from cStringIO import StringIO
import inspect
import sys
import pixiedust

myLogger = pixiedust.getLogger(__name__)

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
        
        decode = 'utf-8'
        parts = templatePath.split("#")
        if len(parts)>1:
            templatePath = parts[0]
            decode = parts[1]
        
        path = self.path + "/" + templatePath
        data = None
        if  decode == "base64":
            myLogger.debug("Loading base64 resource from {0}:{1}".format(module, path))
            with pkg_resources.resource_stream(module, path) as res:
                data = StringIO(res.read()).getvalue().encode('base64')
        else:
            data = pkg_resources.resource_string(module, path ).decode(decode)
        
        return data, templatePath, lambda: False

class PixiedustTemplateEnvironment(object):
    
    def __init__(self, baseModule=None):
        if not baseModule:
            frm = inspect.stack()[1]
            baseModule = inspect.getmodule(frm[0]).__name__
        self.env = Environment(loader=PixiedustTemplateLoader(baseModule),extensions=['jinja2.ext.with_'])
        self.env.filters["oneline"]=lambda s:reduce(lambda s, l: s+l, s.split("\n"), "") if s else s
        self.env.filters["base64dataUri"]=lambda s: 'data:image/png;base64,{0}'.format(self.getTemplate(s+"#base64").render())
        self.env.filters["smartList"]=lambda s: ([s] if type(s) is not list else s)
    
    def from_string(self, source, **kwargs):
        return self.env.from_string(source, globals=kwargs)

    def getTemplate(self, name):
        if ":" in name:
            myLogger.debug("Template already qualified {0}".format(name))
            return self.env.get_template( name )
        visited = {}
        for frm in inspect.stack():
            mod = inspect.getmodule(frm[0])
            s = None if mod is None else mod.__name__
            while s is not None:
                if s not in visited:
                    try:
                        visited[s]=mod
                        return self.env.get_template( s + ":" + name )
                    except (OSError,IOError):
                        #OK if file not found
                        pass
                    except:
                        raise
                n = s.rfind(".")
                s = None if n < 0 else s[:n]
        
        #if we are here, we didn't find it
        raise

    