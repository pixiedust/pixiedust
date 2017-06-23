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
from pixiedust.display.chart.colorManager import Colors
from .bokehBaseDisplay import BokehBaseDisplay
from pixiedust.utils import Logger
import pandas as pd
import numpy
import bokeh.plotting as gridplot
import sys

try:
    from bkcharts import Bar
    from bkcharts.operations import blend
    from bkcharts.attributes import  CatAttr
except ImportError:
    from bokeh.charts import Bar
    from bokeh.charts.operations import blend
    from bokeh.charts.attributes import  CatAttr

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
        keyFields = self.getKeyFields()
        valueFields = self.getValueFields()
        clusterby = self.options.get("clusterby")
        stacked = self.options.get("charttype", "grouped") == "stacked"
        subplots = self.isSubplot()
        workingPDF = self.getWorkingPandasDataFrame().copy()

        def convertPDFDate(df, col):
            #Bokeh doesn't support datetime as index in Bar chart. Convert to String
            if len(keyFields) == 1:
                dtype = df[col].dtype.type if col in df else None
                if numpy.issubdtype(dtype, numpy.datetime64):
                    dateFormat = self.options.get("dateFormat", None)
                    try:
                        df[col] = df[col].apply(lambda x: str(x).replace(':','-') if dateFormat is None else x.strftime(dateFormat))
                    except:
                        self.exception("Error converting dateFormat {}".format(dateFormat))
                        df[col] = df[col].apply(lambda x: str(x).replace(':','-'))

        for index, row in workingPDF.iterrows():
            for k in keyFields:
                if isinstance(row[k], str if sys.version >= '3' else basestring):
                    row[k] = row[k].replace(':', '.')
            workingPDF.loc[index] = row

        charts=[]
        def goChart(label, stack_or_group, values, ylabel=None, color=None):
            convertPDFDate(workingPDF, keyFields[0])
            if ylabel is None:
                ylabel=values
            label=label if isinstance(label, (list, tuple)) else [label]
            if stacked:
                charts.append( Bar(workingPDF, label=CatAttr(columns=label, sort=False), stack=stack_or_group, color=color, values=values, legend=self.showLegend(), ylabel=ylabel))
            else:
                charts.append( Bar(workingPDF, label=CatAttr(columns=label, sort=False), group=stack_or_group, color=color, values=values, legend=self.showLegend(), ylabel=ylabel))

        if clusterby is not None and (subplots or len(valueFields)<=1):
            subplots = subplots if len(valueFields)==1 or subplots else False
            if subplots:
                for j, valueField in enumerate(valueFields):
                    pivot = workingPDF.pivot(
                        index=keyFields[0], columns=clusterby, values=valueField
                    )
                    for i,col in enumerate(pivot.columns[:10]): #max 10
                        data = pd.DataFrame({'values':pivot[col].values, 'names': pivot.index.values})
                        convertPDFDate(data, 'names')
                        if subplots:                        
                            charts.append( 
                                Bar(data, label=CatAttr(columns=['names'], sort=False), color = Colors.hexRGB( 1.*i/2 ), values='values', ylabel=valueField, legend=False, 
                                    title="{0} = {1}".format(clusterby, pivot.columns[i])
                                )
                            )
            else:
                goChart( keyFields[0], clusterby, valueFields[0])
        else:
            if subplots:
                for i,valueField in enumerate(valueFields):
                    goChart( keyFields[0], None, valueField, color=Colors.hexRGB( 1.*i/2 ))
            else:
                if len(valueFields) > 1:
                    series = '_'.join(valueFields)
                    values = blend(*valueFields, name=series.replace('_', ','), labels_name=series)
                else:
                    series = False
                    values = valueFields[0]
                goChart(keyFields, series, values, ylabel=','.join(valueFields))

            if clusterby is not None:
                self.addMessage("Warning: 'Cluster By' ignored when grouped option with multiple Value Fields is selected")
        return charts