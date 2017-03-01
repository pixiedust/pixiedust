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
from pixiedust.display.chart.renderers.baseChartDisplay import commonChartOptions
from .matplotlibBaseDisplay import MatplotlibBaseDisplay
from pixiedust.utils import Logger
import matplotlib.pyplot as plt
import mpld3
import numpy as np

@PixiedustRenderer(id="pieChart")
@Logger()
class PieChartDisplay(MatplotlibBaseDisplay):

    def supportsKeyFieldLabels(self, handlerId):
        return False
    
    def getPreferredDefaultValueFieldCount(self, handlerId):
        return 1

    def getDefaultAggregation(self, handlerId):
        return "COUNT"

    def canStretch(self):
        return False

    # override the default keys displayed when the chart first renders
    def getDefaultKeyFields(self, handlerId, aggregation):
        return self.sampleColumn((aggregation != "COUNT"))

    # override the default values displayed when the chart first renders
    def getDefaultValueFields(self, handlerId, aggregation):
        return self.getDefaultKeyFields(handlerId, aggregation)

    def setChartGrid(self, fig, ax):
        pass

    @commonChartOptions
    def getChartOptions(self):
        return [
            {
                'name': 'legend',
                'description': 'Show legend',
                'metadata': {
                    'type': 'checkbox',
                    'default': "false"
                }
            }
        ]

    def getNumFigures(self):
        return len(self.getValueFields())

    """
        We want height equals to size to make a perfect pie
    """
    def getHeightWidthRatio(self):
        return 1

    """
        return chart width scale factor
    """
    def getWidthScaleFactor(self):
        return 0.6

    def getSubplotHSpace(self):
        return None

    def isStretchingOn(self):
        return True

    def matplotlibRender(self, fig, ax):
        numRows = len(self.getWorkingPandasDataFrame().index)
        if numRows > 20:
            self.addMessage("Too many data points to plot. Dropping {0} rows to make the chart more presentable.".format(numRows-20))
        if not isinstance(ax, (list,np.ndarray)):
            ax=np.array([ax])
        keyFields = self.getKeyFields()
        valueFields = self.getValueFields()
        for i,valueField in enumerate(valueFields):
            pdf = self.getWorkingPandasDataFrame().sort_values(valueField).head(20)
            labels=[ "-".join(map(str, a)) for a in pdf[keyFields].values.tolist() ]
            pdf.plot(
                kind="pie", y = valueField, ax=ax.item(i), labels=labels, 
                autopct='%1.0f%%', subplots=False, legend = self.showLegend()
            )