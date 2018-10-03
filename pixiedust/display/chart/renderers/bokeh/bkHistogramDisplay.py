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
import numpy as np
import math
import sys

@PixiedustRenderer(id="histogram")
@Logger()
class BKHistogramRenderer(BokehBaseDisplay):
    def supportsAggregation(self, handlerId):
        return False

    def supportsKeyFields(self, handlerId):
        return False
    
    def getPreferredDefaultValueFieldCount(self, handlerId):
        return 1

    def getDefaultKeyFields(self, handlerId, aggregation):
        return []

    def acceptOption(self, optionName):
        if optionName == 'histoChartType':
            return False
        return True

    @commonChartOptions
    def getChartOptions(self):
        return [
            { 'name': 'color',
              'metadata': {
                    'type': "dropdown",
                    'values': ["None"] + self.getFieldNames(),
                    'default': ""
                }
            }
        ]

    def canRenderChart(self):
        return (True, None)

    def getExtraFields(self):
        color = self.options.get("color")
        return [color] if color is not None else []

    def createBokehChart(self):
        defaultbin = math.sqrt(len(self.getWorkingPandasDataFrame().index))
        binsize = int(self.options.get('binsize', defaultbin))
        valueFields = self.getValueFields()
        colour = self.options.get("color")

        def histogram(df, vField, color=None, clustered=None):
            colors = self.colorPalette(len(df.index)) if color is None else color

            p = figure(y_axis_label='Frequency', x_axis_label=vField)

            for j,c in enumerate(list(df[clustered].unique())) if clustered else enumerate([None]):
                df2 = df[df[clustered] == c] if c else df
                hist, edges = np.histogram(list(df2[vField]), density=True, bins=binsize)
                p.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], fill_color=colors[j], line_color="#cccccc", fill_alpha=0.8 if clustered else 1, legend=str(c) if clustered else None)

            p.y_range.start=0

            p.legend.location = "top_left"

            hover = HoverTool()
            hover.tooltips = [('Frequency', '@top{0.00}'), ('Interval', '@left - @right')]
            p.add_tools(hover)

            return p

        charts = []
        wpdf = self.getWorkingPandasDataFrame().copy()
        colours = self.colorPalette(None if colour is None else len(wpdf[colour].unique()))
        
        for i, v in enumerate(valueFields):
            charts.append(histogram(wpdf, v, color=colours, clustered=colour))


        return charts

