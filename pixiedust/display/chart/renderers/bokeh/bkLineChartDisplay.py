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
from bokeh.plotting import figure
from bokeh.models import HoverTool
import sys


@PixiedustRenderer(id="lineChart")
@Logger()
class BKLineChartRenderer(BokehBaseDisplay):
    def isSubplot(self):
        return self.options.get("lineChartType", "grouped") == "subplots"

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
        stacked = self.options.get("charttype", "subplots") == "grouped"
        multivalue =  len(valueFields) > 1

        def lineChart(df, xlabel, vFields, color=None, clustered=None, title=None):
            ylabel = ','.join(v for v in vFields)
            x = list(df[xlabel].values)
            if df[xlabel].dtype == object:
                p = figure(y_axis_label=ylabel, x_axis_label=xlabel, title=title, x_range=x, **self.get_common_figure_options())
            else:
                p = figure(y_axis_label=ylabel, x_axis_label=xlabel, title=title, **self.get_common_figure_options())

            if clustered is not None:
                colors = self.colorPalette(len(df[clustered].unique())) if color is None else color
                df[clustered] = df[clustered].astype(str)

                for j,c in enumerate(list(df[clustered].unique())) if clustered else enumerate([None]):
                    df2 = df[df[clustered] == c] if c else df
                    df2 = df2.drop(clustered, axis=1) if c else df2

                    for i,v in enumerate(vFields):
                        y = list(df2[v].values)
                        l = v if self.isSubplot() else c
                        p.line(x, y, line_width=2, color=colors[i] if self.isSubplot() else colors[j], legend=l if self.showLegend() else None)
            else:
                colors = self.colorPalette(len(vFields)) if color is None else color
                

                for i,v in enumerate(vFields):
                    y = list(df[v].values)
                    p.line(x, y, line_width=2, color=colors[i], legend=v if self.showLegend() else None)

            p.legend.location = "top_left"

            hover = HoverTool()
            hover.tooltips = [(xlabel, '@x'), (ylabel, '@y{0.00}'), ('x', '$x'), ('y', '$y')]
            p.add_tools(hover)

            return p

        charts = []
        wpdf = self.getWorkingPandasDataFrame().copy()
        xlabel = keyFields[0] # ','.join(k for k in keyFields)

        for index, row in wpdf.iterrows():
            for k in keyFields:
                if isinstance(row[k], str if sys.version >= '3' else basestring):
                    row[k] = row[k].replace(':', '.')
            wpdf.loc[index] = row

        wpdf.sort_values(xlabel, ascending=[True], inplace=True)

        if self.isSubplot():
            colors = self.colorPalette(len(valueFields)) if len(valueFields) > 1 else self.colorPalette(len(valueFields) * (len(wpdf[clusterby].unique()) if clusterby else len(valueFields)))
            if clusterby:
                for j,c in enumerate(list(wpdf[clusterby].unique())):
                    wpdf2 = wpdf[wpdf[clusterby] == c]
                    charts.append(lineChart(wpdf2, xlabel, valueFields, clustered=clusterby, color=colors, title="{} = {}".format(clusterby, c)))
            else:
                for i, vField in enumerate(valueFields):
                    charts.append(lineChart(wpdf, xlabel, [valueFields[i]], color=colors[i:]))

        elif clusterby and not multivalue:
            charts.append(lineChart(wpdf, xlabel, valueFields, clustered=clusterby))

        else:
            charts.append(lineChart(wpdf, xlabel, valueFields))
            if clusterby:
                self.addMessage("Warning: 'Cluster By' ignored when grouped option with multiple Value Fields is selected")

        return charts
