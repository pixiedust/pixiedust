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

from ..display import DisplayHandlerMeta,registerDisplayHandler,addId
from .downloadCSV import DownloadCSVHandler
from .downloadCloudant import DownloadCloudantHandler
from .downloadSwift import DownloadSwiftHandler

class DownloadMeta(DisplayHandlerMeta):
    @addId
    def getMenuInfo(self,entity):
        clazz = entity.__class__.__name__
        if clazz == "DataFrame":
            return [
                {"categoryId": "Download", "title": "Download as CSV", "icon": "fa-download", "id": "downloadCSV"},
                {"categoryId": "Download", "title": "Stash to Cloudant", "icon": "fa-cloud", "id": "downloadCloudant"},
                {"categoryId": "Download", "title": "Stash to Object Storage", "icon": "fa-suitcase", "id": "downloadSwift"}
            ]
        else:
            return []
    def newDisplayHandler(self,options,entity):
        handlerId = options.get("handlerId")
        if handlerId=="downloadCSV":
            return DownloadCSVHandler(options, entity)
        elif handlerId=="downloadCloudant":
            return DownloadCloudantHandler(option, entity)
        else:
            return DownloadSwiftHandler(options,entity)
        
registerDisplayHandler(DownloadMeta(), system=True)