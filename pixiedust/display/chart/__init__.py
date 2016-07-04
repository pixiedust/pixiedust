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

from .barChartDisplay import BarChartDisplay
from .lineChartDisplay import LineChartDisplay
from .scatterPlotDisplay import ScatterPlotDisplay
from .pieChartDisplay import PieChartDisplay
from .mapChartDisplay import MapChartDisplay
from .histogramDisplay import HistogramDisplay
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
    def newDisplayHandler(self,handlerId,entity):
        if handlerId is None or handlerId=="barChart":
            return BarChartDisplay(entity)
        elif handlerId=="lineChar":
            return LineChartDisplay(entity)
        elif handlerId=="scatterPlot":
            return ScatterPlotDisplay(entity)
        elif handlerId=="pieChart":
            return PieChartDisplay(entity)
        elif handlerId=="mapChart":
            return MapChartDisplay(entity)
        elif handlerId=="histogram":
            return HistogramDisplay(entity)

registerDisplayHandler(ChartDisplayMeta())