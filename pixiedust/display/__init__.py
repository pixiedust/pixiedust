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

from .display import *
import chart,graph,table,tests,download
from pixiedust.utils.printEx import *
import traceback
import warnings
import pixiedust

myLogger=pixiedust.getLogger(__name__ )

def display(entity, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        selectedHandler=getSelectedHandler(kwargs, entity)
        
        myLogger.debug("Creating a new display handler with options {0}: {1}".format(kwargs, selectedHandler))
        displayHandler = selectedHandler.newDisplayHandler(kwargs,entity)
        if displayHandler is None:
            printEx("Unable to obtain handler")
            return
        
        displayHandler.handlerMetadata = selectedHandler    
        displayHandler.callerText = traceback.extract_stack(limit=2)[0][3]
        displayHandler.render()