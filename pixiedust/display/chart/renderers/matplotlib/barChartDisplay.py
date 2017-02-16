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
from pyspark.sql import functions as F
from pixiedust.utils import Logger

@PixiedustRenderer(id="barChart")
@Logger()
class BarChartRenderer(MatplotlibBaseDisplay):

    def getNumFigures(self):
        return len(self.getValueFields()) if self.isSubplot() else 1

    def isSubplot(self):
        return self.options.get("charttype", "grouped") == "subplots"

    #Main rendering method
    def matplotlibRender(self, fig, ax):
        keyFields = self.getKeyFields()
        valueFields = self.getValueFields()
        stacked = self.options.get("charttype", "grouped") == "stacked"
        subplots = self.isSubplot()
        kind = "barh" if self.options.get("orientation", "vertical") == "horizontal" else "bar"

        if len(keyFields) == 1:
            self.getWorkingPandasDataFrame().plot(kind=kind, stacked=stacked, ax=ax, x=keyFields[0], legend=True, subplots=subplots)
        elif len(valueFields) == 1:
            self.getWorkingPandasDataFrame().pivot(
                index=keyFields[0], columns=keyFields[1], values=valueFields[0]
            ).plot(kind=kind, stacked=stacked, ax=ax, legend=True, subplots=subplots)
        else:
            raise Exception("Cannot have multiple keys and values at the same time")