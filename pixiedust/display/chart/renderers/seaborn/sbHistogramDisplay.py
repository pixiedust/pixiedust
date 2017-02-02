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

@PixiedustRenderer(id="histogram")
class sbHistogramDisplay(SeabornBaseDisplay):
  def supportsAggregation(self, handlerId):
    return False

  def supportsLegend(self, handlerId):
    return False

  # TODO: add support for keys
  def supportsKeyFields(self, handlerId):
    return False
  
  def getPreferredDefaultValueFieldCount(self, handlerId):
    return 1

  # no keys by default
  def getDefaultKeyFields(self, handlerId, aggregation):
    return []

  def matplotlibRender(self, fig, ax):
    hist=self.options.get("hist","false") == False
    rug=self.options.get("rug","true") == True
    kde=self.options.get("kde","true") == True

    df = self.getWorkingPandasDataFrame()
    keys = self.getValueFields()

    for key in keys:
      sns.distplot(list(df[key]), ax=ax, kde_kws={"label":"{0} KDE Estim".format(key)}, hist_kws={"label":"{0} Freq".format(key)})


  # def getChartOptions(self):
  #   return [
  #     { 'name': 'rug',
  #       'metadata': {
  #         'type': "checkbox",
  #         'default': "false"
  #       }
  #     },
  #     { 'name': 'hist',
  #       'metadata': {
  #         'type': "checkbox",
  #         'default': "false"
  #       }
  #     },
  #     { 'name': 'kde',
  #       'metadata': {
  #         'type': "checkbox",
  #         'default': "false"
  #       }
  #     }
  #   ]