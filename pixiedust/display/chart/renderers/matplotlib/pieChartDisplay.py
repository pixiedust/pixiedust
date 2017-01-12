# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2016
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
from .matplotlibBaseDisplay import MatplotlibBaseDisplay
import matplotlib.pyplot as plt
import mpld3
import numpy as np

@PixiedustRenderer(id="pieChart")
class PieChartDisplay(MatplotlibBaseDisplay):

    def supportsKeyFieldLabels(self, handlerId):
        return False

    def supportsLegend(self, handlerId):
        return False
    
    def getPreferredDefaultValueFieldCount(self, handlerId):
        return 1

    def getDefaultAggregation(self, handlerId):
        return "COUNT"

    # override the default keys displayed when the chart first renders
    def getDefaultKeyFields(self, handlerId, aggregation):
        return self.sampleColumn((aggregation != "COUNT"))

    # override the default values displayed when the chart first renders
    def getDefaultValueFields(self, handlerId, aggregation):
        return self.getDefaultKeyFields(handlerId, aggregation)

    def setChartGrid(self, fig, ax):
        pass

    def matplotlibRender(self, fig, ax):
        valueFields = self.getValueFields()
        keyFieldValues = self.getKeyFieldValues()
        keyFieldLabels = self.getKeyFieldLabels()
        numPieCharts = len(valueFields)
        colors = self.colormap(np.linspace(0., 1., len(keyFieldValues)))
        if numPieCharts > 1:
            fig.delaxes(ax)
            if numPieCharts < 3:
                pieChartGridPrefix = "1" + str(numPieCharts)
            elif numPieCharts <= 4:
                pieChartGridPrefix = "22"
            else:
                pieChartGridPrefix = str(int(math.ceil(numPieCharts//3))) + "3"
            for i, valueField in enumerate(valueFields):
                ax2 = fig.add_subplot(pieChartGridPrefix + str(i+1))
                patches, texts, autotexts = ax2.pie(valueFieldValues[i], labels=keyFieldLabels, colors=colors, explode=None, autopct='%1.1f%%')
                for j, patch in enumerate(patches):
                    self.connectElementInfo(patch, valueFieldValues[i][j])
                ax2.set_title(valueFields[i], fontsize=18);
                ax2.axis("equal")
                # TODO: hide the x and y axis - this is not working
                ax2.get_xaxis().set_alpha(0)
                ax2.get_yaxis().set_alpha(0)
        else:
            valueFieldValues = self.getValueFieldValueLists()
            patches, texts, autotexts = ax.pie(valueFieldValues[0], labels=keyFieldLabels, colors=colors, explode=None, autopct='%1.1f%%')
            if self.has_mpld3:
                for j, patch in enumerate(patches):
                    self.connectElementInfo(patch, valueFieldValues[0][j])
            ax.set_title(valueFields[0], fontsize=18);
            ax.axis("equal")
            # TODO: hide the x and y axis - this is not working
            ax.get_xaxis().set_alpha(0)
            ax.get_yaxis().set_alpha(0)