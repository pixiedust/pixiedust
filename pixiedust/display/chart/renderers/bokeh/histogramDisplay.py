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
from .bokehBaseDisplay import BokehBaseDisplay
import pixiedust
from bokeh.charts import Histogram, show
from bokeh.layouts import row

myLogger = pixiedust.getLogger(__name__)

@PixiedustRenderer(id="histogram")
class HistogramRenderer(BokehBaseDisplay):
    
    def supportsAggregation(self, handlerId):
        return True

    def supportsLegend(self, handlerId):
        return False

    def supportsKeyFields(self, handlerId):
        return False
    
    def getPreferredDefaultValueFieldCount(self, handlerId):
        return 1

    def getDefaultKeyFields(self, handlerId, aggregation):
        return []

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
        binsize = int(self.options.get('binsize', 10))  
        valueFields = self.getValueFields()
        histograms = []
        if len(valueFields) != 1:
            for i in valueFields:
                histograms.append(Histogram(self.getWorkingPandasDataFrame(), values=i,
            plot_width=400, plot_height=400,bins=binsize, color=self.options.get("color"), 
            xgrid=True, ygrid=True))

            return histograms
        else:
            return Histogram(self.getWorkingPandasDataFrame(), values=self.getValueFields()[0],
            plot_width=400,plot_height=400,bins=binsize, color=self.options.get("color"), 
            xgrid=True, ygrid=True)