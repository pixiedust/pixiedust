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
from .bokehBaseDisplay import BokehBaseDisplay
from pixiedust.utils import Logger
from bokeh.charts import Bar
from bokeh.charts.operations import blend
import bokeh.plotting as gridplot

@PixiedustRenderer(id="barChart")
@Logger()
class BarChartRenderer(BokehBaseDisplay):
    def getSubplotHSpace(self):
        return 0.5

    def isSubplot(self):
        return self.options.get("charttype", "grouped") == "subplots"

    def getExtraFields(self):
        if not self.isSubplot() and len(self.getValueFields())>1:
            #no clusterby if we are grouped and multiValueFields
            return []
    
        clusterby = self.options.get("clusterby")
        return [clusterby] if clusterby is not None else []

    def createBokehChart(self):
        data = self.getWorkingPandasDataFrame()
        keyFields = self.getKeyFields()
        valueFields = self.getValueFields()

        clusterby = self.options.get("clusterby")
        stacked = self.options.get("charttype", "grouped") == "stacked"
        subplots = self.isSubplot()

        # self.debug("keyF={0}, valueF={1}, cluster={2}, stacked={3}".format(keyFields[0], valueFields[0], clusterby, stacked))
        charts = []
        params = []

        if subplots and len(valueFields) > 1:
            for val in valueFields:
                series = clusterby if clusterby is not None else False
                values = val
                params.append((values, series, val))
        elif clusterby is not None and len(valueFields) <= 1:
            params.append((valueFields[0], clusterby, valueFields[0]))
        else:
            series = '_'.join(valueFields)
            values = blend(*valueFields, name=series.replace('_', ','), labels_name=series)
            if clusterby is not None:
                self.addMessage("Warning: 'Cluster By' ignored when you have multiple Value Fields but subplots option is not selected")
            params.append((values, series, ','.join(valueFields)))

        for p in params:
            if stacked:
                b = Bar(data, label=keyFields[0], values=p[0], stack=p[1], legend=self.showLegend(), ylabel=p[2])
            else:
                b = Bar(data, label=keyFields[0], values=p[0], group=p[1], legend=self.showLegend(), ylabel=p[2])

            charts.append(b)

        return charts