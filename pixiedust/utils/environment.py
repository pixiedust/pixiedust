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
import os
import re
import subprocess
from six import with_metaclass
from . import *
from .shellAccess import ShellAccess

class Environment(with_metaclass( 
        type("",(type,),{
            "__getattr__":lambda cls, key: getattr(cls.env, key)
        }), object
    )):

    class _Environment(object):
        @property
        @cache(fieldName="_scalaVersion")
        def scalaVersion(self):
            scala = "{0}{1}bin{1}scala".format(self.scalaHome, os.sep)
            try:
                scala_out = subprocess.check_output([scala, "-version"], stderr=subprocess.STDOUT).decode("utf-8")
            except subprocess.CalledProcessError as cpe:
                scala_out = cpe.output
            match = re.search(".*version[^0-9]*([0-9]*[^.])\.([0-9]*[^.])\.([0-9]*[^.]).*", str(scala_out))
            if match and len(match.groups()) > 2:
                return int(match.group(1)), int(match.group(2))
            else:
                raise EnvironmentError("Unable to compute Scala Version")

        @property
        @cache(fieldName="_scalaHome")
        def scalaHome(self):
            return os.environ.get("SCALA_HOME")

        @property
        @cache(fieldName="_javaClassPath")
        def javaClassPath(self):
            from pixiedust.utils.javaBridge import JavaWrapper
            return JavaWrapper("java.lang.System").getProperty("java.class.path")

        @property
        @cache(fieldName="_isRunningOnDSX")
        def isRunningOnDSX(self):
            envVar = os.environ.get("RUNTIME_ENV_STOREFRONT")
            return envVar is not None and envVar.startswith("bluemix/")

        @property
        @cache(fieldName="_pixiedustHome")
        def pixiedustHome(self):
            return os.environ.get("PIXIEDUST_HOME", os.path.expanduser('~'))

        @property
        @cache(fieldName="_hasSpark")
        def hasSpark(self):
            try:
                from pyspark import SparkContext
                return ShellAccess["sc"] is not None or ShellAccess["spark"] is not None
            except ImportError:
                return False

        @property
        @cache(fieldName="_sparkVersion")
        def sparkVersion(self):
            if not self.hasSpark:
                return None
            try:
                spark_handle = ShellAccess["sc"] if "sc" in ShellAccess else ShellAccess["spark"]
                if spark_handle is None:
                    return None
                version = spark_handle.version
                if version.startswith('1.'):
                    return 1
                elif version.startswith('2.'):
                    return 2
            except Exception as exc:
                raise Exception("Unable to read spark Version, please check your install {}".format(exc))
            return None

    env = _Environment()

"""
Decorator for functions that can be called from Scala Notebook by adding the fromScala keyword argument to the decorated function
"""
def scalaGateway(func):
    def wrapper(*args,**kwargs):
        fromScala = False
        if "fromScala" in kwargs:
            kwargs.pop("fromScala")
            fromScala = True
        retValue = func(*args, **kwargs)
        if fromScala and retValue is not None:
            from pixiedust.utils.javaBridge import JavaWrapper
            from pixiedust.utils.scalaBridge import ConverterRegistry
            import uuid
            id = str(uuid.uuid4())[:8]
            JavaWrapper("com.ibm.pixiedust.Pixiedust").addEntity( id, ConverterRegistry.toJava( retValue )[0] )
            return id
        return retValue
    return wrapper
