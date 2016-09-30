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

from ..display.display import DisplayHandlerMeta,PixiedustDisplay,addId

from .stashCloudant import StashCloudantHandler
from .stashSwift import StashSwiftHandler
import pixiedust.utils.dataFrameMisc as dataFrameMisc

@PixiedustDisplay(system=True)
class StashMeta(DisplayHandlerMeta):
    @addId
    def getMenuInfo(self,entity):
        if dataFrameMisc.isPySparkDataFrame(entity):
            return [
                {"categoryId": "Download", "title": "Stash to Cloudant", "icon": "fa-cloud", "id": "stashCloudant"},
                {"categoryId": "Download", "title": "Stash to Object Storage", "icon": "fa-suitcase", "id": "stashSwift"}
            ]
        else:
            return []
    def newDisplayHandler(self,options,entity):
        handlerId = options.get("handlerId")
        if handlerId=="stashCloudant":
            return StashCloudantHandler(options, entity)
        else:
            return StashSwiftHandler(options,entity)
