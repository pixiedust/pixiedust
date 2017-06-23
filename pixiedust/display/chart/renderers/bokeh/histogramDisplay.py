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
from pixiedust.display.chart.colorManager import Colors
from .bokehBaseDisplay import BokehBaseDisplay
from pixiedust.utils import Logger
from bokeh.layouts import row
import math

try:
    from bkcharts import Histogram, show
except ImportError:
    from bokeh.charts import Histogram, show

@PixiedustRenderer(id="histogram")
@Logger()
class HistogramRenderer(BokehBaseDisplay):
    
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
        plotwidth = int(self.getPreferredOutputWidth()/2)
        plotheight = int(self.getPreferredOutputHeight() * 0.75)
        defaultbin = math.sqrt(len(self.getWorkingPandasDataFrame().index))
        binsize = int(self.options.get('binsize', defaultbin))
        valueFields = self.getValueFields()
        histograms = []
        if len(valueFields) != 1:
            for i,valueField in enumerate(valueFields):
                color = self.options.get("color")
                if color is None:
                    color = Colors.hexRGB( 1.*i/2 )
                histograms.append(Histogram(
                    self.getWorkingPandasDataFrame(), values=valueField, plot_width=plotwidth, plot_height=plotheight,bins=binsize, 
                    color=color, xgrid=True, ygrid=True, ylabel='Frequency')
                )
            return histograms
        else:
            return Histogram(self.getWorkingPandasDataFrame(), values=self.getValueFields()[0],
            bins=binsize, color=self.options.get("color"), 
            xgrid=True, ygrid=True, ylabel='Frequency')