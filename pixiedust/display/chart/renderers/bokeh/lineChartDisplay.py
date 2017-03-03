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
from pixiedust.display.chart.colorManager import Colors
from .bokehBaseDisplay import BokehBaseDisplay
from pixiedust.utils import Logger
from bokeh.charts import Line
from bokeh.palettes import Spectral11
from bokeh.plotting import figure

@PixiedustRenderer(id="lineChart")
@Logger()
class LineChartRenderer(BokehBaseDisplay):
    # def supportsAggregation(self, handlerId):
    #     return False

    def createBokehChart2(self):
        keyFields = self.getKeyFields()
        valueFields = self.getValueFields()
        data = self.getWorkingPandasDataFrame()
        subplots = self.options.get("lineChartType", "grouped") == "subplots"
        clusterby = self.options.get("clusterby")

        figs = []

        if clusterby is None:
            if subplots:
                for i,valueField in enumerate(valueFields):
                    figs.append(Line(data, x = keyFields[0], y=valueField, color = Colors.hexRGB( 1.*i/2 ), legend=self.showLegend(), plot_width=int(800/len(valueFields))))
            else:
                figs.append(Line(data, x = keyFields[0], y=valueFields, color=valueFields, legend=self.showLegend()))
        else:
            if subplots:
                self.addMessage("Warning: 'Cluster By' ignored when you have multiple Value Fields but subplots options selected")
                for i, valueField in enumerate(valueFields):
                    figs.append(Line(data, x = keyFields[0], y=valueField, color = Colors.hexRGB( 1.*i/2 ), legend=self.showLegend(), plot_width=int(800/len(valueFields))))
            else:
                if len(valueFields) > 1:
                    self.addMessage("Warning: 'Cluster By' ignored when you have multiple Value Fields but subplots option is not selected")
                else:
                    self.addMessage("Warning: 'Cluster By' ignored when grouped option with multiple Value Fields is selected")
                figs.append(Line(data, x = keyFields[0], y=valueFields, color=valueFields, legend=self.showLegend()))
        return figs

    def isSubplot(self):
        return self.options.get("lineChartType", "grouped") == "subplots"

    def getExtraFields(self):
        if not self.isSubplot() and len(self.getValueFields())>1:
            #no clusterby if we are grouped and multiValueFields
            return []
    
        clusterby = self.options.get("clusterby")
        return [clusterby] if clusterby is not None else []

    def createBokehChart(self):
        keyFields = self.getKeyFields()
        valueFields = self.getValueFields()
        clusterby = self.options.get("clusterby")
        subplots = self.isSubplot()

        charts=[]
        if clusterby is not None and (subplots or len(valueFields)<=1):
            subplots = subplots if len(valueFields)==1 or subplots else False
            if not subplots:
                fig = figure()
                charts.append(fig)
            for j, valueField in enumerate(valueFields):
                pivot = self.getWorkingPandasDataFrame().pivot(
                    index=keyFields[0], columns=clusterby, values=valueField
                )
                for i,col in enumerate(pivot.columns[:10]): #max 10
                    if subplots:
                        charts.append( Line(pivot[str(col)], color=Colors.hexRGB( 1.*i/2 ), ylabel=valueField, xlabel=keyFields[0], legend=self.showLegend()))
                    else:
                        fig.line(x = pivot.index.values, y = pivot[str(col)].values, color = Colors.hexRGB( 1.*i/2 ), legend=col if self.showLegend() else None)
        else:
            if subplots:
                for i,valueField in enumerate(valueFields):
                    charts.append(Line(self.getWorkingPandasDataFrame(), x = keyFields[0], y=valueField, color = Colors.hexRGB( 1.*i/2 ), legend=self.showLegend(), plot_width=int(800/len(valueFields))))
            else:
                charts.append(Line(self.getWorkingPandasDataFrame(), x = keyFields[0], y=valueFields, color=valueFields, legend=self.showLegend()))

            if clusterby is not None:
                self.addMessage("Warning: 'Cluster By' ignored when grouped option with multiple Value Fields is selected")
        return charts