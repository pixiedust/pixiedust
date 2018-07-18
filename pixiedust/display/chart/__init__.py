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

from ..display import *
from pixiedust.utils.dataFrameAdapter import *
from pixiedust.display.chart.renderers import PixiedustRenderer
from pixiedust.display.streaming import StreamingDataAdapter
import pixiedust

myLogger = pixiedust.getLogger(__name__ )

#bootstrap all the renderers
renderers = ["matplotlib", "bokeh", "seaborn", "mapbox", "google", "brunel", "table"]

for renderer in renderers:
    try:
        __import__("pixiedust.display.chart.renderers." + renderer)
    except Exception as exc:
        myLogger.warn("Unable to import renderer {0}: {1}".format(renderer, str(exc)))

@PixiedustDisplayMeta()
class ChartDisplayMeta(DisplayHandlerMeta):
    @addId
    def getMenuInfo(self, entity, dataHandler):
        if dataHandler is not None:
            # first item in this array will be the default renderer (if no metadata exists)
            infos = [
                {"categoryId": "Table", "title": "Table.Next", "icon": "fa-table", "id": "tableView"},
                {"categoryId": "Chart", "title": "Bar Chart", "icon": "fa-bar-chart", "id": "barChart"},
                {"categoryId": "Chart", "title": "Line Chart", "icon": "fa-line-chart", "id": "lineChart"},
                {"categoryId": "Chart", "title": "Scatter Plot", "icon": "fa-circle", "id": "scatterPlot"},
                {"categoryId": "Chart", "title": "Pie Chart", "icon": "fa-pie-chart", "id": "pieChart"},
                {"categoryId": "Chart", "title": "Map", "icon": "fa-globe", "id": "mapView"},
                {"categoryId": "Chart", "title": "Histogram", "icon": "fa-area-chart", "id": "histogram"}
            ]

            infos = [info for info in infos if info["id"] in PixiedustRenderer.getHandlerIdList(dataHandler.isStreaming)]
            accept = getattr(dataHandler, "accept", lambda id: True)
            if not callable(accept):
                accept = lambda id:True
            
            return [info for info in infos if accept(info["id"]) is True]

        return []

    def newDisplayHandler(self, options, entity, dataHandler):
        return PixiedustRenderer.getRenderer(options, entity, dataHandler.isStreaming)