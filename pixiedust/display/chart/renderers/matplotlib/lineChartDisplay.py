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
import matplotlib.pyplot as plt
import numpy as np
from pixiedust.utils import Logger

@PixiedustRenderer(id="lineChart")
@Logger()
class LineChartDisplay(MatplotlibBaseDisplay):

    def getNumFigures(self):
        return len(self.getValueFields()) if self.isSubplot() else 1

    def isSubplot(self):
        return self.options.get("lineChartType", None) == "subplots"

    def matplotlibRender(self, fig, ax):
        subplots = self.isSubplot()
        self.getWorkingPandasDataFrame().plot(
            kind='line', x=self.getKeyFields(), y=self.getValueFields(), ax=ax, subplots=subplots, legend=True,
            logx=self.getBooleanOption("logx", False), logy=self.getBooleanOption("logy",False)
        )
        if self.useMpld3:
            #import mpld3
            #tooltip = mpld3.plugins.PointLabelTooltip(lines[0], labels=ys)
            #mpld3.plugins.connect(fig, tooltip)
            #FIXME
            pass