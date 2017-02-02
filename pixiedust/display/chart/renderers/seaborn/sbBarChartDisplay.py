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
from .seabornBaseDisplay import SeabornBaseDisplay
import pixiedust
import numpy as np
import pandas as pd
import seaborn as sns

myLogger = pixiedust.getLogger(__name__)

@PixiedustRenderer(id="barChart")
class sbBarChartDisplay(SeabornBaseDisplay):
  def renderStacked(self, ax):
    pandaList = self.getPandasValueFieldValueLists()
    valueFieldValues = pandaList if len(pandaList) >= 1 else []
    key = self.getKeyFields()[0]
    colors = ['#79c36a','#f1595f','#599ad3','#f9a65a','#9e66ab','#cd7058','#d77fb3','#727272']

    data = self.sumDfList(valueFieldValues, [key], "agg")

    for i in range(1, len(self.getValueFields())):
      # myLogger.info("data[{0}]:\r\n{1}".format(str(i), data))
      sns.barplot(x=key, y='agg', data=data, ax=ax, color=colors[i])
      data = self.minusDf(data, valueFieldValues[i], [key], "agg")

    # myLogger.info("data[]:\r\n{0}\r\n{1} , {2}".format(data, x, y))
    sns.barplot(x=key, y='agg', data=valueFieldValues[0], ax=ax, color=colors[0])

  def renderGrouped(self, ax):
    keyFields = self.getKeyFields()
    valueFields = self.getValueFields()
    orient = self.options.get("orientation", None)

    df = self.getWorkingPandasDataFrame()
    cols = df.columns.values.tolist()
    selectedcols = np.concatenate([keyFields, valueFields])

    for col in cols:
      if col not in selectedcols:
        df.drop(col, axis=1, inplace=True)

    df1 = pd.melt(df, id_vars=keyFields).sort_values(['variable','value'])
    sns.barplot(x=keyFields[0], y='value', hue='variable', ax=ax, data=df1)

  def getChartContext(self, handlerId):
    return ('barChartOptionsDialogBody.html', {})

  def matplotlibRender(self, fig, ax):
    data = None
    x = None
    y = None
    stacked = self.options.get("stacked", "true") == "true"
    if len(self.getValueFields())>1 and stacked:
      self.renderStacked(ax)
    elif len(self.getValueFields())>1:
      self.renderGrouped(ax)
    else:
      self.renderStacked(ax)

  # def getChartOptions(self):
  #   return [
  #     { 'name': 'orientation',
  #       'metadata': {
  #         'type': "dropdown",
  #         'values': ["h", "v"],
  #         'default': "v"
  #       }
  #     }
  #   ]

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

  # def sumzip(self,x,y):
  #   return [sum(values) for values in zip(x,y)]

  # def minuszip(self,x,y):
  #   return [values[0]-values[1] for values in zip(x,y)]

  # def sumtotal(self, x):
  #   y = np.zeros(len(x[0]))
  #   for i in range(len(x)):
  #     y = self.sumzip(y, x[i])
  #   return y