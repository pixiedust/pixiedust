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
from pyspark import SparkContext
from pyspark.sql import SQLContext, DataFrame
import py4j.java_gateway
import sys

"""
class used to redirect Java JVM System output to Python notebook
It implements a Java interface that will be used as a callback from the java side
"""
class PixiedustOutput(object):
    def printOutput(self, s):
        print(s)
        
    class Java:
        implements = ["com.ibm.pixiedust.PixiedustOutputListener"]

"""
Helper class for making it easier to call Java code from Python
"""
sc = SparkContext.getOrCreate()
class JavaWrapper(object): 
    def __init__(self, objectIdentifier, captureOutput=False):
        if isinstance(objectIdentifier, str if sys.version >= '3' else basestring):
            self.jHandle = self._getJavaHandle(objectIdentifier)
        else:
            self.jHandle=objectIdentifier
        self.captureOutput(captureOutput)
        
    def captureOutput(self, doIt):
        if doIt:
            pixiedustOutputSink = JavaWrapper("com.ibm.pixiedust.PixiedustOutputStream").jHandle(PixiedustOutput())
            JavaWrapper("scala.Console").setOut(pixiedustOutputSink)
            #TODO: find a way to redirect system.out output for the current execution of the call
            #JavaWrapper("java.lang.System").setOut(pixiedustOutputSink)
            sc._gateway.start_callback_server()

    def __getattr__(self, name):
        o = self.jHandle.__getattr__(name)
        return o
        
    def _getJavaHandle(self,fqName):
        parts = fqName.split(".")
        handle = sc._jvm
        for package in parts:
            handle = handle.__getattr__(package)
        try:
            handle = handle.__getattr__("MODULE$")
        except:
            handle = handle
        return handle

    '''
    use direct Java Reflection to run a method. This is needed because in case of dynamically loaded classes, Py$j automatic reflexion doesn't
    work right
    '''
    def callMethod(self, methodName, *args):
        argLen = len(args)
        jMethodParams = None if argLen == 0 else sc._gateway.new_array(sc._jvm.Class, argLen )
        jMethodArgs = None if argLen == 0 else sc._gateway.new_array(sc._jvm.Object, argLen )
        for i,arg in enumerate(args):
            jMethodParams[i] = arg.getClass()
            jMethodArgs[i] = arg
        #get the method and invoke it
        return self.jHandle.getClass().getMethod(methodName, jMethodParams).invoke(self.jHandle, jMethodArgs)

"""
Misc helper functions
"""
def pd_getJavaSparkContext():
    return sc._jsc.sc()

def pd_convertFromJava(entity):
    if ( entity.__class__.__name__ == "JavaMember"):
        entity = entity()
    if entity.__class__.__name__ == "JavaObject":
        javaClassName = entity.getClass().getName()
        if javaClassName == "org.apache.spark.sql.DataFrame":
            return DataFrame(entity, SQLContext(sc, entity.sqlContext()))