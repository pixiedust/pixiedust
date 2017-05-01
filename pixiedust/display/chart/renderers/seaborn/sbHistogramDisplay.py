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
from pixiedust.display.chart.colorManager import Colors
from pixiedust.utils import Logger
import numpy as np
import pandas as pd
import seaborn as sns
import math

@PixiedustRenderer(id="histogram")
@Logger()
class sbHistogramDisplay(SeabornBaseDisplay):
    def supportsAggregation(self, handlerId):
        return False

    # TODO: add support for keys
    def supportsKeyFields(self, handlerId):
        return False
  
    def getPreferredDefaultValueFieldCount(self, handlerId):
        return 1

    # no keys by default
    def getDefaultKeyFields(self, handlerId, aggregation):
        return []

    def canRenderChart(self):
        return (True, None)

    def getNumFigures(self):
        return len(self.getValueFields())

    def acceptOption(self, optionName):
        if optionName == 'histoChartType':
            return False
        return True

    def matplotlibRender(self, fig, ax):
        rug=self.options.get("rug","false") == "true"
        kde=self.options.get("kde","true") == "true"
        defaultbin = math.sqrt(len(self.getWorkingPandasDataFrame().index))
        binsize = int(self.options.get('binsize', defaultbin))

        def plot(ax, valueField=None, color=None):
            data = self.getWorkingPandasDataFrame()[valueField]
            sns.distplot( data, ax=ax, bins=binsize, rug=rug, kde=kde,
                kde_kws={"label":"{0} KDE Estim".format(valueField)}, hist_kws={"label":"{0} Freq".format(valueField)},
                label=valueField,color = color
            )

        if len(self.getValueFields()) > 1:
            for j, valueField in enumerate(self.getValueFields()):
                plot(self.getAxItem(ax, j), valueField, Colors.colormap(1.*j/2))
        else:
            plot(ax, self.getValueFields()[0])

    @commonChartOptions
    def getChartOptions(self):
        return [{
            'name': 'rug',
            'description': 'Rugplot',
            'metadata': {
                'type': "checkbox",
                'default': "false"
            }
        },{ 
            'name': 'kde',
            'description': 'Kernel Density',
            'metadata': {
                'type': "checkbox",
                'default': "false"
            }
        }]