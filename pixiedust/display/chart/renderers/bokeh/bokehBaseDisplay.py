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

from pixiedust.display.display import CellHandshake
from pixiedust.display.chart.renderers import PixiedustRenderer
from ..baseChartDisplay import BaseChartDisplay
from six import with_metaclass
from abc import abstractmethod, ABCMeta
from bokeh.plotting import figure, output_notebook
from bokeh.models.tools import *
from bokeh.io import notebook_div

import pixiedust
myLogger = pixiedust.getLogger(__name__)

@PixiedustRenderer(rendererId="bokeh")
class BokehBaseDisplay(with_metaclass(ABCMeta, BaseChartDisplay)):
    CellHandshake.addCallbackSniffer( lambda: "{'nostore_bokeh':!!window.Bokeh}")

    """
    Default implementation for creating a chart object.
    """
    def createBokehChart(self):
        return figure()

    def cleanList(self, l):
        if l is None or len(l) == 0:
            return[]
        return l if len(l)>1 else l[0]

    def doRenderChart(self):
        clientHasBokeh = self.options.get("nostore_bokeh", "false") == "true"
        if not clientHasBokeh:          
            output_notebook(hide_banner=True)
        charts = self.createBokehChart()

        if not isinstance(charts, list):
            charts.add_tools(ResizeTool())
            charts.title = self.options.get("title", "")
            charts.grid.grid_line_alpha=0.3
            return notebook_div(charts)
        else:
            from bokeh.layouts import gridplot
            return notebook_div(gridplot(charts, ncols=2))