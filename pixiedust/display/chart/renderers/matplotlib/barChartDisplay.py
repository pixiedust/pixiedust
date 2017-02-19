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

    def getExtraFields(self):
        self.debug("in getExtraFields")
        if not self.isSubplot() and len(self.getValueFields())>1:
            #no categorizeby if we are grouped and multiValueFields
            self.debug("got nothing")
            return []
    
        categorizeby = self.options.get("categorizeby")
        self.debug("categorizeby {}".format(categorizeby))
        return [categorizeby] if categorizeby is not None else []

    #Main rendering method
    def matplotlibRender(self, fig, ax):
        keyFields = self.getKeyFields()
        valueFields = self.getValueFields()
        stacked = self.options.get("charttype", "grouped") == "stacked"
        subplots = self.isSubplot()
        kind = "barh" if self.options.get("orientation", "vertical") == "horizontal" else "bar"
        categorizeby = self.options.get("categorizeby")

        if categorizeby is not None and (subplots or len(valueFields)<=1):
            for j, valueField in enumerate(valueFields):
                pivot = self.getWorkingPandasDataFrame().pivot(
                    index=keyFields[0], columns=categorizeby, values=valueField
                )
                pivot.index.name=valueField
                pivot.plot(kind=kind, stacked=stacked, ax=self.getAxItem(ax, j), legend=True, label=valueField)
        else:
            self.getWorkingPandasDataFrame().plot(kind=kind, stacked=stacked, ax=ax, x=keyFields[0], legend=True, subplots=subplots)

            if categorizeby is not None:
                self.addMessage("Warning: 'Categorize By' ignored when you have multiple Value Fields but subplots option is not selected")