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
from pixiedust.utils.dataFrameAdapter import *
import pixiedust.utils.dataFrameMisc as dataFrameMisc

@PixiedustDisplay()
class ChartDisplayMeta(DisplayHandlerMeta):
    @addId
    def getMenuInfo(self,entity):
        if dataFrameMisc.isPySparkDataFrame(entity) or dataFrameMisc.isPandasDataFrame(entity):
            return [
                {"categoryId": "Chart", "title": "Bar Chart", "icon": "fa-bar-chart", "id": "barChart"},
                {"categoryId": "Chart", "title": "Line Chart", "icon": "fa-line-chart", "id": "lineChart"},
                {"categoryId": "Chart", "title": "Scatter Plot", "icon": "fa-circle", "id": "scatterPlot"},
                {"categoryId": "Chart", "title": "Pie Chart", "icon": "fa-pie-chart", "id": "pieChart"},
                {"categoryId": "Chart", "title": "Map", "icon": "fa-globe", "id": "mapChart"},
                {"categoryId": "Chart", "title": "Histogram", "icon": "fa-table", "id": "histogram"}
            ]
        else:
            return []
    def newDisplayHandler(self,options,entity):
        handlerId=options.get("handlerId")
        entity=createDataframeAdapter(entity)
        if handlerId is None or handlerId=="barChart":
            return BarChartDisplay(options,entity)
        elif handlerId=="lineChart":
            return LineChartDisplay(options,entity)
        elif handlerId=="scatterPlot":
            return ScatterPlotDisplay(options,entity)
        elif handlerId=="pieChart":
            return PieChartDisplay(options,entity)
        elif handlerId=="mapChart":
            return MapChartDisplay(options,entity)
        elif handlerId=="histogram":
            return HistogramDisplay(options,entity)