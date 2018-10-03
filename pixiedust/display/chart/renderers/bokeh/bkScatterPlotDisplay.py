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

from pixiedust.display.chart.renderers import PixiedustRenderer
from pixiedust.display.chart.renderers.baseChartDisplay import commonChartOptions
from pixiedust.utils import Logger

from .bokehBaseDisplay import BokehBaseDisplay
from bokeh.plotting import figure
from bokeh.models import HoverTool
import sys


@PixiedustRenderer(id="scatterPlot")
@Logger()
class BKScatterPlotRenderer(BokehBaseDisplay):
    def supportsAggregation(self, handlerId):
        return False

    @commonChartOptions
    def getChartOptions(self):
        return [
            { 'name': 'color',
              'metadata': {
                    'type': "dropdown",
                    'values': ["None"] + [f for f in self.getFieldNames() if f not in self.getKeyFields() and f not in self.getValueFields()],
                    'default': ""
                },
              'validate': lambda option:\
                    (option in self.getFieldNames() and option not in self.getKeyFields() and option not in self.getValueFields(),\
                    "color value is already used in keys or values for this chart")
            }
        ]

    def canRenderChart(self):
        valueFields = self.getValueFields()
        if len(valueFields) != 1:
            return (False, "Can only specify one Value Field")

        #Verify that all key field are numericals
        for keyField in self.getKeyFields():
            if not self.dataHandler.isNumericField(keyField):
                return (False, "Column {0} is not numerical".format(keyField))
        
        return (True, None)

    def getExtraFields(self):
        color = self.options.get("color")
        return [color] if color is not None else []

    def createBokehChart(self):
        keyFields = self.getKeyFields()
        valueFields = self.getValueFields()
        color = self.options.get("color")
        xlabel = keyFields[0]
        ylabel = valueFields[0]

        wpdf = self.getWorkingPandasDataFrame().copy()
        colors = self.colorPalette(None if color is None else len(wpdf[color].unique()))
        
        p = figure(y_axis_label=ylabel, x_axis_label=xlabel)

        for i,c in enumerate(list(wpdf[color].unique())) if color else enumerate([None]):
            wpdf2 = wpdf[wpdf[color] == c] if c else wpdf
            p.circle(list(wpdf2[xlabel]), list(wpdf2[ylabel]), color=colors[i], legend=str(c) if c and self.showLegend() else None, fill_alpha=0.5, size=8)


        p.xaxis.axis_label = xlabel
        p.yaxis.axis_label = ylabel
        p.legend.location = "top_left"

        hover = HoverTool()
        hover.tooltips = [(xlabel, '@x'), (ylabel, '@y')]
        p.add_tools(hover)

        return p

