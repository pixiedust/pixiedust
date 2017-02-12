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
        labels = self.getKeyFieldLabels()
        subplots = len(self.getKeyFieldValues()) > 1
        self.getWorkingPandasDataFrame().plot(kind="pie", ax=ax, labels=labels, autopct='%1.0f%%', subplots=subplots)
        ax.axis("equal")