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
import os
import subprocess
from IPython.core.magic import (Magics, magics_class, cell_magic)
from pixiedust.utils.javaBridge import *
from pixiedust.utils.template import *

'''
Manages the variables defined interactively in the Notebook
'''
class InteractiveVariables(object):
    def __init__(self, shell):
        self.shell = shell

    def varTypeTransformer(self, varName, varValue):
        pythonToScalaTypeMap = {
            "str":"String","int":"Int"
        }
        scalaType = pythonToScalaTypeMap.get(varValue.__class__.__name__, None)
        if scalaType == "String":
            varValue = "\"" + varValue + "\""
        return {"value": varValue, "codeValue": varValue if scalaType is not None else None, "type": scalaType or "Any"}

    def getVarsDict(self):
        user_ns = self.shell.user_ns
        user_ns_hidden = self.shell.user_ns_hidden
        nonmatching = object()  # This can never be in user_ns
        #for i in user_ns:
        #    print(user_ns[i].__class__)
        filtered = ["function"]
        out = { key : self.varTypeTransformer(key, user_ns[key]) for key in user_ns \
                if not key.startswith('_') \
                and (user_ns[key] is not user_ns_hidden.get(key, nonmatching)) \
                and not inspect.isclass(user_ns[key])\
                and not inspect.isfunction(user_ns[key])\
                and not inspect.ismodule(user_ns[key])}
        return out

@magics_class
class PixiedustScalaMagics(Magics):
    def __init__(self, shell):
        super(PixiedustScalaMagics,self).__init__(shell)
        self.interactiveVariables = InteractiveVariables(shell)
        self.scala_home = os.environ.get("SCALA_HOME")
        self.class_path = JavaWrapper("java.lang.System").getProperty("java.class.path")
        self.env = PixiedustTemplateEnvironment()

    def hasLineOption(self, line, option):
        return option in line

    @cell_magic
    def scala(self, line, cell):
        if not self.scala_home:
            print("Error Cannot run scala code: SCALA_HOME environment variable not set")
            return
        
        #generate the code
        scalaCode = self.env.getTemplate("scalaCell.template").render(
            cell=cell, variables=self.interactiveVariables.getVarsDict()
        )
        if self.hasLineOption(line, "debug"):
            print(scalaCode)
            return
        
        #build the scala object
        dir=os.path.expanduser('~') + "/pixiedust"
        if not os.path.exists(dir):
            os.makedirs(dir)
        source="pixiedustRunner.scala"
        with open(dir + "/" + source, "w") as f:
            f.write(scalaCode)
        #Compile the code
        proc = subprocess.Popen([self.scala_home + "/bin/scalac","-classpath", self.class_path, source],stdout=subprocess.PIPE,stderr=subprocess.PIPE, cwd=dir)
        code = proc.wait()
        if code != 0:
            while True:
                line = proc.stderr.readline()
                if not line:
                    break
                print(line.rstrip())
            return
        
        #Load the class and initialize the variables
        f = sc._jvm.java.io.File(dir)
        url = f.toURL()
        urls=sc._gateway.new_array(sc._jvm.java.net.URL,1)
        urls[0]=url

        cl = sc._jvm.java.net.URLClassLoader(urls)
        cls = sc._jvm.java.lang.Class.forName("com.ibm.pixiedust.PixiedustScalaRun$", True, cl)
        
        runnerObject = JavaWrapper(cls.getField("MODULE$").get(None), True)
        runnerObject.callMethod("initSC", pd_getJavaSparkContext() )
        runnerObject.callMethod("runCell")

        #discard the ClassLoader, we only use it within the context of a cell.
        #TODO: change that when we support inline scala class/object definition
        cl.close()
        cl=None
        cls=None
        runnerObject=None

get_ipython().register_magics(PixiedustScalaMagics)
