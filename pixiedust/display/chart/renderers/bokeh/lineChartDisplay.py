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
from bokeh.palettes import Spectral11
from bokeh.plotting import figure

@PixiedustRenderer(id="lineChart")
@Logger()
class LineChartRenderer(BokehBaseDisplay):
    def supportsAggregation(self, handlerId):
        return False

    def createBokehChart(self):
        keyFields = self.getKeyFields()
        valueFields = self.getValueFields()
        data = self.getWorkingPandasDataFrame().sort_values(keyFields[0])
        subplots = self.options.get("lineChartType", "grouped") == "subplots"
        clusterby = self.options.get("clusterby")

        figs = []

        if clusterby is None:
            if subplots:
                for valueField in valueFields:
                    figs.append(Line(data, x = keyFields[0], y=valueField, legend=self.showLegend(), plot_width=int(800/len(valueFields))))
            else:
                figs.append(Line(data, x = keyFields[0], y=valueFields, color=valueFields, legend=self.showLegend()))
        else:
            if subplots:
                self.addMessage("Warning: 'Cluster By' ignored when you have multiple Value Fields but subplots options selected")
                for valueField in valueFields:
                    figs.append(Line(data, x = keyFields[0], y=valueField, legend=self.showLegend(), plot_width=int(800/len(valueFields))))
            else:
                if len(valueFields) > 1:
                    self.addMessage("Warning: 'Cluster By' ignored when you have multiple Value Fields but subplots option is not selected")
                else:
                    self.addMessage("Warning: 'Cluster By' ignored when grouped option with multiple Value Fields is selected")
                figs.append(Line(data, x = keyFields[0], y=valueFields, color=valueFields, legend=self.showLegend()))


        return figs