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
from . import storage
import pkg_resources
import binascii
import shutil
from . import pdLogging

storage._initStorage()

#Misc helper methods
def fqName(entity):
    return (entity.__module__ + "." if hasattr(entity, "__module__") else "") + entity.__class__.__name__

#init scala bridge, make sure that correct pixiedust.jar is installed

jarDirPath = os.environ.get("PIXIEDUST_HOME", os.path.expanduser('~')) + "/data/libs/"
jarFilePath = jarDirPath + "pixiedust.jar"

dir = os.path.dirname(jarDirPath)
if not os.path.exists(dir):
    os.makedirs(dir)

def installPixiedustJar():
    with pkg_resources.resource_stream(__name__, "resources/pixiedust.jar") as resJar:
        with open( jarFilePath, 'wb+' ) as installedJar:
            shutil.copyfileobj(resJar, installedJar)
            print("Pixiedust runtime updated. Please restart kernel")

copyFile = True
if os.path.isfile(jarFilePath):
    with open( jarFilePath, 'rb' ) as installedJar:
        installedCRC = binascii.crc32( installedJar.read() )
        with pkg_resources.resource_stream(__name__, "resources/pixiedust.jar") as resJar:
            copyFile = installedCRC != binascii.crc32( resJar.read() )

if copyFile:
    installPixiedustJar()

"""
Helper decorator that automatically cache results of a class method into a field
"""
def cache(fieldName):
    def outer(func):
        if fieldName == func.__name__:
            raise AttributeError("cached fieldName cannot have the same name as the function: {}".format(fieldName))
        def inner(cls, *args, **kwargs):
            if hasattr(cls, fieldName) and getattr(cls, fieldName) is not None:
                return getattr(cls, fieldName)
            retValue = func(cls, *args, **kwargs)
            setattr(cls, fieldName, retValue)
            return retValue
        return inner
    return outer

"""
Helper decorator that automatically add Logging capability to a class
"""
class Logger(object):
    def __call__(self, cls, *args, **kwargs):
        if not hasattr(cls, "myLogger"):
            cls.myLogger = pdLogging.getLogger(cls.__module__ + "." + cls.__name__)
            cls.debug = cls.myLogger.debug
            cls.warn = cls.myLogger.warn
            cls.error = cls.myLogger.error
            cls.info = cls.myLogger.info
            cls.exception = cls.myLogger.exception
        return cls
