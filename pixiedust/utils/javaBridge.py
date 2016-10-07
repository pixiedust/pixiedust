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
import pixiedust

myLogger = pixiedust.getLogger(__name__)

"""
class used to redirect Java JVM System output to Python notebook
It implements a Java interface that will be used as a callback from the java side
"""
class PixiedustOutput(object):
    def printOutput(self, s):
        print(s)

    def sendChannel(self, channel, data):
        self.printOutput(channel + " : " + data)
        
    class Java:
        implements = ["com.ibm.pixiedust.PixiedustOutputListener"]

"""
Helper class for making it easier to call Java code from Python
"""
sc = SparkContext.getOrCreate()
class JavaWrapper(object): 
    def __init__(self, objectIdentifier, captureOutput=False, outputChannel = None, outputReceiverClassName = None):
        if isinstance(objectIdentifier, str if sys.version >= '3' else basestring):
            self.jHandle = self._getJavaHandle(objectIdentifier)
        else:
            self.jHandle=objectIdentifier
        self.outputChannel = self.createClass(outputChannel) or PixiedustOutput()
        self.outputReceiver = JavaWrapper(outputReceiverClassName) if outputReceiverClassName is not None else None
        self.captureOutput(captureOutput)

    def createClass(self, className):
        if className is None or className == False:
            return None
        #extract module
        index = className.rfind(".")
        moduleName = None
        if index > 0:
            moduleName = className[:index]
            className = className[index+1:]

        __import__(moduleName)
        return getattr(sys.modules[moduleName], className)()
        
    def captureOutput(self, doIt):
        if doIt:
            if self.outputReceiver and self.outputChannel and self.outputReceiver.hasMethod("setChannelListener", sc._jvm.java.lang.Class.forName("com.ibm.pixiedust.PixiedustOutputListener")):
                self.outputReceiver.setChannelListener(self.outputChannel)
            else:
                pixiedustOutputSink = JavaWrapper("com.ibm.pixiedust.PixiedustOutputStream").jHandle(self.outputChannel)
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

    def hasMethod(self, methodName, *args):
        return self.getMethod(methodName, *args) != None

    def getMethods(self):
        return self.jHandle.getClass().getMethods()

    def getMethod(self, methodName, *args):
        argLen = len(args)
        jMethodParams = None if argLen == 0 else sc._gateway.new_array(sc._jvm.Class, argLen )
        for i,arg in enumerate(args):
            jMethodParams[i] = arg if arg.getClass().getName() == "java.lang.Class" else arg.getClass()

        try:
            return self.jHandle.getClass().getMethod(methodName, jMethodParams)
        except:
            return None

    '''
    use direct Java Reflection to run a method. This is needed because in case of dynamically loaded classes, Py$j automatic reflexion doesn't
    work right
    '''
    def callMethod(self, methodName, *args):
        myLogger.debug("Calling callMethod: methodName: {0}".format(methodName))
        argLen = len(args)
        jMethodParams = None if argLen == 0 else sc._gateway.new_array(sc._jvm.Class, argLen )
        jMethodArgs = None if argLen == 0 else sc._gateway.new_array(sc._jvm.Object, argLen )
        for i,arg in enumerate(args):
            jMethodParams[i] = (arg if arg.__class__.__name__ == "JavaClass" else arg.getClass())
            jMethodArgs[i] = arg
        #find the method and invoke it
        for m in self.jHandle.getClass().getMethods():
            if m.getName() == methodName and len(m.getParameterTypes()) == argLen:
                myLogger.debug("Found method with Name {0}".format(methodName))
                #Check the arguments type match
                match=True
                if argLen > 0:
                    for m1,m2 in zip( m.getParameterTypes(), jMethodParams ):
                        if not m1.isAssignableFrom(m2):
                            myLogger.debug("Found method {0} with arguments that are not matching".format(methodName))
                            match = False
                            break;
                if match:
                    return m.invoke(self.jHandle, jMethodArgs)
        
        raise ValueError("Method {0} that matches the given arguments not found".format(methodName) )
        #return self.jHandle.getClass().getMethod(methodName, jMethodParams).invoke(self.jHandle, jMethodArgs)

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