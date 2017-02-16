# coding=utf-8
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
from pixiedust.display.chart.renderers.baseChartDisplay import commonChartOptions
from .seabornBaseDisplay import SeabornBaseDisplay
from pixiedust.utils import Logger
import numpy as np
import pandas as pd
import seaborn as sns

@PixiedustRenderer(id="barChart")
@Logger()
class sbBarChartDisplay(SeabornBaseDisplay):
    def renderStacked(self, ax):
        pandaList = self.getWorkingPandasDataFrame()
        valueFieldValues = pandaList if len(pandaList) >= 1 else []
        key = self.getKeyFields()[0]
        colors = ['#79c36a','#f1595f','#599ad3','#f9a65a','#9e66ab','#cd7058','#d77fb3','#727272']

        #data = self.sumDfList(valueFieldValues, [åkey], "agg")

        for i, valueField in enumerate(self.getValueFields()):
            sns.barplot(x=key, y=valueField, data=self.getWorkingPandasDataFrame(), ax=ax, color=colors[i], orient=self.getOrientation() )
            #data = self.minusDf(data, valueFieldValues[i], [key], "agg")

        #sns.barplot(x=key, y='agg', data=self.getWorkingPandasDataFrame(), ax=ax, color=colors[0])

    def renderGrouped(self, ax):
        keyFields = self.getKeyFields()
        valueFields = self.getValueFields()

        df = self.getWorkingPandasDataFrame()
        cols = df.columns.values.tolist()
        selectedcols = np.concatenate([keyFields, valueFields])

        for col in cols:
            if col not in selectedcols:
                df.drop(col, axis=1, inplace=True)

        df1 = pd.melt(df, id_vars=keyFields).sort_values(['variable','value'])
        sns.barplot(x=keyFields[0], y='value', hue='variable', ax=ax, data=df1, orient=self.getOrientation())

    def matplotlibRender(self, fig, ax):
        data = None
        x = None
        y = None
        stacked = self.options.get("stacked", "false") == "true"
        if len(self.getValueFields())>1 and stacked:
            self.renderStacked(ax)
        elif len(self.getValueFields())>1:
            self.renderGrouped(ax)
        else:
            self.renderStacked(ax)

    def getOrientation(self):
        return "v" if self.options.get("orientation", "vertical") == "vertical" else "h"
  
    @commonChartOptions
    def getChartOptions(self):
        options = []
        if len(self.getValueFields()) > 1:
            options.insert(0,
                {
                'name': 'stacked',
                'description': 'Stacked Bar Chart',
                'metadata': {
                    'type': 'checkbox',
                    'default': "false"
                }
                }
            )
        return options

    def sumDfList(self, list, groupby, column):
        data = None
        for df in list:
            if data is None:
                data = df
            else:
                data = pd.concat([data, df]).groupby(groupby, as_index=False)[column].sum()
        return data

    def minusDf(self, minuend, subtrahend, groupby, column):
        return pd.concat([minuend, subtrahend]).groupby(groupby, as_index=False)[column].agg(np.subtract)