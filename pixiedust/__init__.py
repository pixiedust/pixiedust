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

__all__=['packageManager','display','services','utils']
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    #shortcut to logging
    import pixiedust.utils as utils
    import pixiedust.utils.pdLogging
    logger = utils.pdLogging.getPixiedustLogger()
    getLogger = utils.pdLogging.getLogger

    #shortcut to packageManager
    import pixiedust.packageManager as packageManager
    printAllPackages=packageManager.printAllPackages
    installPackage=packageManager.installPackage
    uninstallPackage=packageManager.uninstallPackage

    import pixiedust.display
    import pixiedust.services

    #automated import into the user namespace
    try:
        get_ipython().user_ns["display"]=display.display

        #javaBridge and scalaBridge only work in the driver, not an executor
        from pixiedust.utils.javaBridge import *
        from pixiedust.utils.scalaBridge import *

        #shortcut to Spark job monitoring
        from pixiedust.utils.sparkJobProgressMonitor import enableSparkJobProgressMonitor
        enableJobMonitor = enableSparkJobProgressMonitor
    except NameError:
        #IPython not available we must be in a spark executor
        pass