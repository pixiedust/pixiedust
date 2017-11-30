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

import math
from pixiedust.display.chart.renderers import PixiedustRenderer
from pixiedust.utils import Logger
from .brunelBaseDisplay import BrunelBaseDisplay

@PixiedustRenderer(id="histogram")
@Logger()
class HistogramRenderer(BrunelBaseDisplay):
    def supportsAggregation(self, handlerId):
        return False

    def supportsKeyFields(self, handlerId):
        return False
    
    def getPreferredDefaultValueFieldCount(self, handlerId):
        return 1

    def getDefaultKeyFields(self, handlerId, aggregation):
        return []

    def acceptOption(self, optionName):
        if optionName == 'histoChartType':
            return False
        return True

    def compute_brunel_magic(self):
        parts = ["bar"]
        defaultbin = math.sqrt(len(self.getWorkingPandasDataFrame().index))
        binsize = int(self.options.get('binsize', defaultbin))

        for index, key in enumerate(self.getValueFields()):
            if index > 0:
                parts.append("+ bar")
            parts.append("x({0}) bin({0}:{1})".format(key, binsize))
            parts.append("y(#count)")
            parts.append("""style("size:100%")""")
        return parts
