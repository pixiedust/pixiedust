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
from pixiedust.display.display import *
from pixiedust.display import addDisplayRunListener

#add a display Run Listener 
addDisplayRunListener( lambda entity, options: onNewDisplayRun(entity, options) )

activesStreamingEntities = {}
def onNewDisplayRun(entity, options):
    if "cell_id" in options and "showchrome" in options:
        if options["cell_id"] in activesStreamingEntities:
            del activesStreamingEntities[options["cell_id"]]

class StreamingDisplay(Display):
    def __init__(self, options, entity, dataHandler=None):
        super(StreamingDisplay,self).__init__(options,entity,dataHandler)
        self.windowSize = 100