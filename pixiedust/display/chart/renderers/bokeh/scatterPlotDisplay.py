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
from .bokehBaseDisplay import BokehBaseDisplay
import pixiedust
from bokeh.charts import Scatter

myLogger = pixiedust.getLogger(__name__)

@PixiedustRenderer(id="scatterPlot")
class ScatterPlotRenderer(BokehBaseDisplay):

    def supportsAggregation(self, handlerId):
        return False
    
    def supportsLegend(self, handlerId):
        return False

    def supportsKeyFields(self, handlerId):
        return False

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
        valueFields = self.getValueFields()
        if len(valueFields) < 2:
            return (False, "At least two numerical columns required.")
        else:
            return (True, None)

    def getExtraFields(self):
        color = self.options.get("color")
        return [color] if color is not None else []

    def createBokehChart(self):        
        data = self.getWorkingPandasDataFrame()
        return Scatter(data, 
            x = self.getValueFields()[0], y = self.getValueFields()[1],
            xlabel=self.getValueFields()[0],ylabel=self.getValueFields()[1],legend="top_left", plot_width=800,color=self.options.get("color"))