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
from bokeh.charts import Bar

myLogger = pixiedust.getLogger(__name__)

@PixiedustRenderer(id="barChart")
class BarChartRenderer(BokehBaseDisplay):
    def getChartContext(self, handlerId):
        return ('barChartOptionsDialogBody.html', {})

    def createBokehChart(self):
        pandaList = self.getPandasValueFieldValueLists()
        data = pandaList[0] if len(pandaList) >= 1 else []

        stacked = self.options.get("stacked", "true") == "true"
        group = None
        stack = None
        color = self.getKeyFields()[0]
        if len(self.getKeyFields())>1:
            color = self.getKeyFields()[1]
            if stacked:
                stack = self.getKeyFields()
            else:
                group = self.getKeyFields()
        
        agg=(self.getAggregation() or "count").lower()
        if agg == 'avg':
            agg = 'mean'

        return Bar(data, values='agg', agg=agg, label=self.getKeyFields()[0], group=group, stack=stack, legend=None, 
            color=color, plot_width=800)