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
from .matplotlibBaseDisplay import MatplotlibBaseDisplay
from pixiedust.display.chart.colorManager import Colors
import matplotlib.pyplot as plt
import mpld3
import numpy as np
import pixiedust
import math

myLogger = pixiedust.getLogger(__name__)

@PixiedustRenderer(id="histogram")
class HistogramDisplay(MatplotlibBaseDisplay):

    def supportsAggregation(self, handlerId):
        return False

    # TODO: add support for keys
    def supportsKeyFields(self, handlerId):
        return False
    
    def getPreferredDefaultValueFieldCount(self, handlerId):
        return 1

    # no keys by default
    def getDefaultKeyFields(self, handlerId, aggregation):
        return []

    def getNumFigures(self):
        return len(self.getValueFields()) if self.isSubplots() else 1

    def isSubplots(self):
        return len(self.getValueFields()) > 1 and self.options.get("histoChartType", "stacked") == "subplots"

    def canRenderChart(self):
        return (True, None)

    def matplotlibRender(self, fig, ax):
        stacked = len(self.getValueFields()) > 1 and self.options.get("histoChartType", "stacked") == "stacked"
        subplots = self.isSubplots()
        defaultbin = math.sqrt(len(self.getWorkingPandasDataFrame().index))
        binsize = int(self.options.get('binsize', defaultbin))

        def plot(ax, valueField=None, color=None):
            data = self.getWorkingPandasDataFrame() if valueField is None else self.getWorkingPandasDataFrame()[valueField]
            data.plot(
                kind="hist", stacked=stacked, ax=ax, bins=binsize, legend=self.showLegend(), x = valueField,
                label=valueField,color = color, colormap = None if color else Colors.colormap
            )

        if subplots:
            for j, valueField in enumerate(self.getValueFields()):
                plot(self.getAxItem(ax, j), valueField, Colors.colormap(1.*j/2))
        else:
            plot(ax)