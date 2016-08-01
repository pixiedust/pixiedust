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

from .display import GraphDisplay
from ..display import *

@PixiedustDisplay()
class GraphDisplayMeta(DisplayHandlerMeta):
    @addId
    def getMenuInfo(self,entity):
        clazz = entity.__class__.__name__
        if clazz == "GraphFrame":
            #Check that we have a longitude and latitude in the vertices dataframe
            fnames=[sf.name for sf in entity.vertices.schema.fields]
            ret = []
            if "longitude" in fnames and "latitude" in fnames:
                ret.append({"categoryId": "Graph", "title": "Graph Map", "icon":"fa-map-marker", "id":"graphMap"})
            ret.append({"categoryId": "Graph", "title": "Node-Link Graph", "icon":"fa-map-marker", "id":"nodeLinkGraph"})
            return ret
        
        return []
            
    def newDisplayHandler(self,options,entity):
        return GraphDisplay(options,entity)
