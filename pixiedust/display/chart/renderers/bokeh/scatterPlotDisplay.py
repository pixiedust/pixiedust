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
from pixiedust.utils import Logger

try:
    from bkcharts import Scatter
except ImportError:
    from bokeh.charts import Scatter

@PixiedustRenderer(id="scatterPlot")
@Logger()
class ScatterPlotRenderer(BokehBaseDisplay):

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
        data = self.getWorkingPandasDataFrame()
        return Scatter(data, 
            x = self.getKeyFields()[0], y = self.getValueFields()[0],
            xlabel=self.getKeyFields()[0],ylabel=self.getValueFields()[0],legend=self.showLegend(), color=self.options.get("color"))