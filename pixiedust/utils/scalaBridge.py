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

@magics_class
class PixiedustScalaMagics(Magics):
    def __init__(self, shell):
        super(PixiedustScalaMagics,self).__init__(shell)
        self.interactiveShell = InteractiveVariable(shell)
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

        scalaCode = self.env.getTemplate("scalaCell.template").render(cell=cell)
        if self.hasLineOption(line, "debug"):
            print(scalaCode)
            return
        
        #build the scala object
        dir="/Users/dtaieb/temp"
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

'''
Manages the variables defined interactively in the Notebook
'''
class InteractiveVariable(object):
    def __init__(self, shell):
        self.shell = shell