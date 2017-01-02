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
import numpy as np
import pandas as pd
from itertools import product
from pyspark.sql import functions as F
import pixiedust
from pixiedust.utils.shellAccess import ShellAccess
from functools import reduce

myLogger = pixiedust.getLogger(__name__)

@PixiedustRenderer(id="barChart")
class BarChartRenderer(MatplotlibBaseDisplay):

    def getChartContext(self, handlerId):
        return ('barChartOptionsDialogBody.html', {})

    #Main rendering method
    def matplotlibRender(self, fig, ax):
        stacked = self.options.get("stacked", "true") == "true"
        grouped = not stacked
        if len(self.getKeyFields())>1 and grouped:
            self.generateGroupedSeries(fig, ax)
        elif grouped == False and len(self.getValueFields())>1:
            self.generateStackedBarChart(fig, ax)           
        else:
            self.generateBarChart(fig, ax)

    def generateBarChart(self, fig, ax):
        keyFieldValues = self.getKeyFieldValues()
        valueFields = self.getValueFields()
        numColumns = len(keyFieldValues)
        barWidth = min(0.35, 0.9/len(valueFields))
        x_intv = np.arange(numColumns)
        for i, valueField in enumerate(valueFields):
            valueFieldValues = self.getValueFieldValueLists()
            bar = ax.bar(x_intv+(i*barWidth), valueFieldValues[i], barWidth, color=self.colormap(1.*i/numColumns), alpha=0.5, label=valueField)
            if self.has_mpld3:
                self.connectElementInfo(bar, valueFieldValues[i])
        plt.xticks(x_intv+(barWidth/2), self.getKeyFieldLabels() )
        plt.xlabel(", ".join(self.getKeyFields()), fontsize=18)

    def generateStackedBarChart(self, fig, ax):
        keyFieldValues = self.getKeyFieldValues()
        valueFieldValues = self.getValueFieldValueLists()
        valueFields = self.getValueFields()
        numColumns = len(keyFieldValues)
        barWidth = 0.35
        x_intv = np.arange(numColumns)
        bar = ax.bar(x_intv, valueFieldValues[0], barWidth, alpha=0.5, label=valueFields[0])
        if self.has_mpld3:
            self.connectElementInfo(bar, valueFieldValues[0])
        colors= ['#79c36a','#f1595f','#599ad3','#f9a65a','#9e66ab','#cd7058','#d77fb3','#727272']
        bottom=valueFieldValues[0]
        for i in range(1,len(valueFields)):
            bar = plt.bar(x_intv, valueFieldValues[i], barWidth, label=valueFields[i], color=colors[i], bottom=bottom)
            if self.has_mpld3:       
                self.connectElementInfo(bar, valueFieldValues[i])
        bottom = self.sumzip(bottom, valueFieldValues[i])

    def generateGroupedSeries(self, fig, ax):
        def safeRepr(o):
            import decimal
            if isinstance(o, decimal.Decimal):
                return float(o)
            return o
        # convert to pandas
        pdf = self.entity.toPandas()

        # fill in gaps
        vals = []
        for keyField in self.getKeyFields():
            vals.append(pdf[keyField].unique())
        pdf2 = pd.DataFrame(list(product(*vals)), columns=self.getKeyFields() )
        pdf = pd.merge(pdf,pdf2, on=self.getKeyFields(), how='outer').fillna(0)

        # convert back to sql dataframe (fillna required)
        df = ShellAccess.sqlContext.createDataFrame(pdf).fillna(0)
        valueFields = self.getValueFields()
        keyFields = self.getKeyFields()
        selectedValueField = valueFields[0]
        series = df.rdd.map(lambda r: (safeRepr(r[0]), [( safeRepr(r[1]), safeRepr(r[selectedValueField]))]))\
            .reduceByKey(lambda x,y: x+y)\
            .map(lambda r: (r[0], sorted(r[1], key=lambda tup: tup[0])))\
            .sortByKey()\
            .collect()
        maxLen=reduce(lambda x,y: max(x, len(y[1])), series, 0)
        ind=np.arange(len(series))
        #FIXME: generate random colors
        colors= ['#79c36a','#f1595f','#599ad3','#f9a65a','#9e66ab','#cd7058','#d77fb3','#727272']
        for i in range(maxLen):
            data=[t[1][i][1] if i<len(t[1]) else 0 for t in series]
            bars = ax.bar(ind + (i*0.15), data, width=0.15, color=colors[i], label=series[0][1][i][0])
            if self.has_mpld3:
                self.connectElementInfo(bars, data)
        plt.xticks(ind+0.3, [str(x[0]) for x in series])
        plt.ylabel(valueFields[0])
        plt.xlabel(keyFields[0])

        self.titleLegend=keyFields[1]

    def sumzip(self,x,y):
        return [sum(values) for values in zip(x,y)]