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

__all__=['packageManager','display','services','utils']

import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")

    try:
        #Check if we have an python shell available, if not, use our ProxyShell
        get_ipython()
    except NameError:
        from .proxyShell import ProxyInteractiveShell
        ProxyInteractiveShell.instance()   

    #shortcut to logging
    import pixiedust.utils.pdLogging as pdLogging
    logger = pdLogging.getPixiedustLogger()
    getLogger = pdLogging.getLogger

    from pixiedust.utils.environment import Environment
    if Environment.hasSpark:
        #shortcut to packageManager
        import pixiedust.packageManager as packageManager
        printAllPackages=packageManager.printAllPackages
        installPackage=packageManager.installPackage
        uninstallPackage=packageManager.uninstallPackage

        try:
            from py4j.protocol import Py4JJavaError
            #javaBridge and scalaBridge only work in the driver, not an executor
            from pixiedust.utils.javaBridge import *
            from pixiedust.utils.scalaBridge import *

            #shortcut to Spark job monitoring
            from pixiedust.utils.sparkJobProgressMonitor import enableSparkJobProgressMonitor
            enableJobMonitor = enableSparkJobProgressMonitor
        except (NameError, Py4JJavaError):
            #IPython not available we must be in a spark executor
            pass

    #automated import into the user namespace
    try:
        from IPython.core.getipython import get_ipython
        from pixiedust.display import display
        import pixiedust.services
        if "display" not in get_ipython().user_ns:
            #be nice, only set the display variable on the user namespace if it's not already taken
            get_ipython().user_ns["display"]=display

        from pixiedust.utils.sampleData import sampleData
        import pixiedust.apps.debugger
        from pixiedust.utils import checkVersion
        from pixiedust.utils.storage import optOut, optIn
        checkVersion()
    except (NameError):
        #IPython not available we must be in a spark executor
        pass
