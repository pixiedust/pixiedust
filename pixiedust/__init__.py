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

#shortcut to logging
import utils
import utils.pdLogging
logger = utils.pdLogging.getPixiedustLogger()
getLogger = utils.pdLogging.getLogger

#shortcut to packageManager
import packageManager
printAllPackages=packageManager.printAllPackages
installPackage=packageManager.installPackage
uninstallPackage=packageManager.uninstallPackage

import display
import services
from utils.javaBridge import *
from utils.scalaBridge import *

#automated import into the user namespace
try:
    get_ipython().user_ns["display"]=display.display
except NameError:
    #IPython not available we must be in a spark executor
    pass