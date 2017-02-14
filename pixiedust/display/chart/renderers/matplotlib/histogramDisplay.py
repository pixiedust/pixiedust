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
import pixiedust

myLogger = pixiedust.getLogger(__name__)

@PixiedustRenderer(id="histogram")
class HistogramDisplay(MatplotlibBaseDisplay):

    def supportsAggregation(self, handlerId):
        return False

    def supportsLegend(self, handlerId):
        return False

    # TODO: add support for keys
    def supportsKeyFields(self, handlerId):
        return False
    
    def getPreferredDefaultValueFieldCount(self, handlerId):
        return 1

    # no keys by default
    def getDefaultKeyFields(self, handlerId, aggregation):
        return []        

    def matplotlibRender(self, fig, ax):
        stacked = len(self.getValueFields()) > 1
        binsize = int(self.options.get('binsize', 10))
        self.getWorkingPandasDataFrame().plot(kind="hist", stacked=stacked, ax=ax, bins=binsize)