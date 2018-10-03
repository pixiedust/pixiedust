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
import numpy as np
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, FactorRange, HoverTool
from bokeh.core.properties import value as bk_value
from bokeh.transform import factor_cmap
import sys


@PixiedustRenderer(id="barChart")
@Logger()
class BKBarChartRenderer(BokehBaseDisplay):
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
        multivalue =  len(valueFields) > 1

        def convertPDFDate(df, col):
            #Bokeh doesn't support datetime as index in Bar chart. Convert to String
            if len(keyFields) == 1:
                dtype = df[col].dtype.type if col in df else None
                if np.issubdtype(dtype, np.datetime64):
                    dateFormat = self.options.get("dateFormat", None)
                    try:
                        df[col] = df[col].apply(lambda x: str(x).replace(':','-') if dateFormat is None else x.strftime(dateFormat))
                    except:
                        self.exception("Error converting dateFormat {}".format(dateFormat))
                        df[col] = df[col].apply(lambda x: str(x).replace(':','-'))

        def stackedBar(df, xlabel, vFields, color=None, clustered=False, title=None):
            ylabel = ','.join(v for v in vFields)
            ystart = 0

            if clustered:
                factors=list(df.index)
                l = [ bk_value(a) for a in list(df.index) ]
                data = {'pd_stacked_col': list(df.columns.values)}
                for x in list(df.index):
                    data[x] = list(df[x:x].values[0])
                    ystart = min(ystart, min(data[x]))
            else:
                factors=vFields
                l = [ bk_value(a) for a in vFields ]
                data = {'pd_stacked_col': list(df[xlabel].values)}
                for v in vFields:
                    data[v] = list(df[v].values)
                    ystart = min(ystart, min(data[v]))
            
            src = ColumnDataSource(data)
            colors = self.colorPalette(len(factors)) if color is None else color

            p = figure(x_range=data['pd_stacked_col'], y_axis_label=ylabel, x_axis_label=xlabel, title=title)
            p.vbar_stack(factors, x='pd_stacked_col', width=0.9, source=src, legend=l if self.showLegend() else None, color=colors)

            p.y_range.start = ystart
            p.axis.minor_tick_line_color = None
            p.outline_line_color = None
            p.x_range.range_padding = 0.1
            p.xaxis.major_label_orientation = 1
            p.xgrid.grid_line_color = None
            p.legend.location = "top_left"

            hover = HoverTool()
            hover.tooltips = [(d if d is not 'pd_stacked_col' else xlabel, '@' + d + '{0.00}') for d in data]
            p.add_tools(hover)

            return p

        def groupedBar(df, xlabel, vFields, color=None, clustered=False, title=None):
            ylabel = ','.join(v for v in vFields)

            if clustered:
                factors=list(df.index)
                x = [ (b, a) for b in list(df.columns.values) for a in list(df.index) ]
                l = [ (a) for b in list(df.columns.values) for a in list(df.index) ]
                counts = sum(zip(df.at[a,b] for b in list(df.columns.values) for a in list(df.index)), ())
            else:
                factors=vFields
                x = [ (b,a) for b in list(df[xlabel].values) for a in vFields ]
                l = [ (a) for b in list(df[xlabel].values) for a in vFields ]
                counts = [ df[df[xlabel] == b][a].values[0] for b in list(df[xlabel].values) for a in vFields ]

            src = ColumnDataSource(data=dict(x=x, counts=counts, l=l))
            colors = self.colorPalette(len(factors)) if color is None else color

            p = figure(x_range=FactorRange(*x), y_axis_label=ylabel, x_axis_label=xlabel, title=title)
            p.vbar(x='x', top='counts', width=0.925, source=src, legend='l' if self.showLegend() else None, color=factor_cmap('x', palette=colors, factors=factors, start=1, end=2))

            p.y_range.start = 0 if not counts else min(0, min(counts))
            p.axis.minor_tick_line_color = None
            p.outline_line_color = None
            p.x_range.range_padding = 0.1
            p.xaxis.major_label_orientation = 1
            p.xaxis.major_label_text_font_size = "0px"
            p.xaxis.major_label_text_color = None
            p.xaxis.major_tick_line_color = None
            p.xgrid.grid_line_color = None
            p.legend.location = "top_left"

            hover = HoverTool()
            hover.tooltips = [(xlabel, '@x'), (ylabel, '@counts{0.00}')]
            p.add_tools(hover)

            return p

        charts = []
        wpdf = self.getWorkingPandasDataFrame().copy()
        xlabel = ','.join(k for k in keyFields)

        for index, row in wpdf.iterrows():
            for k in keyFields:
                if isinstance(row[k], str if sys.version >= '3' else basestring):
                    row[k] = row[k].replace(':', '.')
            wpdf.loc[index] = row

        if len(keyFields) > 1:
            wpdf[xlabel] = wpdf[keyFields].apply(lambda x: ','.join(str(y) for y in x), axis=1)
        else:
            wpdf[xlabel] = wpdf[xlabel].astype(str)

        if self.isSubplot():
            colors = self.colorPalette(len(valueFields) * (len(wpdf[clusterby].unique())) if clusterby else len(valueFields))
            k = 0
            for i, valueField in enumerate(valueFields):
                for j,c in enumerate(list(wpdf[clusterby].unique())) if clusterby else enumerate([None]):
                    wpdf2 = wpdf[wpdf[clusterby] == c] if c else wpdf
                    wpdf2 = wpdf2.drop(clusterby, axis=1) if c else wpdf2
                    charts.append(stackedBar(wpdf2, xlabel, [valueFields[i]], clustered=False, color=colors[k], title="{} = {}".format(clusterby, c) if c else None))
                    k += 1

        elif clusterby and not multivalue:
            ylabel = ','.join(v for v in valueFields)
            wpdf[clusterby] = wpdf[clusterby].astype(str)
            wpdf = wpdf.pivot(clusterby, xlabel, ylabel)
            wpdf = wpdf.fillna(0)

            if stacked:
                charts.append(stackedBar(wpdf, xlabel, valueFields, clustered=True))
            else:
                charts.append(groupedBar(wpdf, xlabel, valueFields, clustered=True))

        else:
            if stacked:
                charts.append(stackedBar(wpdf, xlabel, valueFields, clustered=False))
            else:
                charts.append(groupedBar(wpdf, xlabel, valueFields, clustered=False))

            if clusterby:
                self.addMessage("Warning: 'Cluster By' ignored when grouped option with multiple Value Fields is selected")

        return charts
