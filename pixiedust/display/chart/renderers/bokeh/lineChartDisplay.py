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
from pixiedust.utils import Logger
from bokeh.charts import Line

@PixiedustRenderer(id="lineChart")
@Logger()
class LineChartRenderer(BokehBaseDisplay):
    def supportsAggregation(self, handlerId):
        return False

    def createBokehChart(self):
        keyFields = self.getKeyFields()
        valueFields = self.getValueFields()
        data = self.getWorkingPandasDataFrame().sort_values(keyFields[0])
        figs = []
        for valueField in valueFields:
            figs.append(Line(data, x = self.getKeyFields()[0], y=valueField, legend=None, plot_width=int(800/len(valueFields))))

        return figs