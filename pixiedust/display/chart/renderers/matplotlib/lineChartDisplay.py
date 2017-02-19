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
from pixiedust.display.chart.renderers.colors import Colors
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

    def getExtraFields(self):
        if not self.isSubplot() and len(self.getValueFields())>1:
            #no categorizeby if we are grouped and multiValueFields
            return []
    
        categorizeby = self.options.get("categorizeby")
        return [categorizeby] if categorizeby is not None else []

    def matplotlibRender(self, fig, ax):
        subplots = self.isSubplot()
        keyFields = self.getKeyFields()
        valueFields = self.getValueFields()

        categorizeby = self.options.get("categorizeby")
        if categorizeby is not None and (subplots or len(valueFields)<=1):
            gp = self.getWorkingPandasDataFrame().set_index(categorizeby).groupby(level=categorizeby)
            for j, valueField in enumerate(valueFields):
                for i, (label, df) in enumerate(gp):
                    df.plot(
                        kind="line", ax=self.getAxItem(ax, j), x=keyFields, y=valueField, label=label, legend=True, colors = Colors[1.*i/len(gp)],
                        logx=self.getBooleanOption("logx", False), logy=self.getBooleanOption("logy",False)
                    )
        else:
            self.getWorkingPandasDataFrame().plot(
                kind='line', x=keyFields, y=valueFields, ax=ax, subplots=subplots, legend=True, colormap = Colors.colormap,
                logx=self.getBooleanOption("logx", False), logy=self.getBooleanOption("logy",False)
            )

            if categorizeby is not None:
                self.addMessage("Warning: 'Categorize By' ignored when grouped option with multiple Value Fields is selected")
        
        if self.useMpld3:
            #import mpld3
            #tooltip = mpld3.plugins.PointLabelTooltip(lines[0], labels=ys)
            #mpld3.plugins.connect(fig, tooltip)
            #FIXME
            pass