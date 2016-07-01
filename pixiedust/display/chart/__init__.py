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

from .display import ChartDisplay
from ..display import *

class ChartDisplayMeta(DisplayHandlerMeta):
    @addId
    def getMenuInfo(self,entity):
        clazz = entity.__class__.__name__
        if clazz == "DataFrame":
            return [
                {"categoryId": "Chart", "title": "Bar Chart", "icon": "fa-bar-chart", "id": "barChart"},
                {"categoryId": "Chart", "title": "Line Chart", "icon": "fa-line-chart", "id": "lineChart"},
                {"categoryId": "Chart", "title": "Scatter Plot", "icon": "fa-table", "id": "scatterPlot"},
                {"categoryId": "Chart", "title": "Pie Chart", "icon": "fa-pie-chart", "id": "pieChart"},
                {"categoryId": "Chart", "title": "Map", "icon": "fa-map", "id": "mapChart"},
                {"categoryId": "Chart", "title": "Histogram", "icon": "fa-table", "id": "histogram"}
            ]
        else:
            return []
    def newDisplayHandler(self,entity):
        return ChartDisplay(entity)

registerDisplayHandler(ChartDisplayMeta())