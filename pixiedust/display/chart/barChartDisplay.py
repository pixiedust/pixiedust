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

from .display import ChartDisplay
from .mpld3ChartDisplay import Mpld3ChartDisplay
import matplotlib.pyplot as plt
import numpy as np
import mpld3.plugins as plugins
from mpld3 import utils
from pyspark.sql import functions as F
import mpld3
from .plugins.dialog import DialogPlugin
from random import randint


class BarChartDisplay(Mpld3ChartDisplay):
    
    def getChartContext(self, handlerId):
        return ('barChartOptionsDialogBody.html', {})
    
    def doRenderMpld3(self, handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues):
        grouped = (self.options.get("stacked") == "false")
        if(grouped == False and len(valueFieldValues)>1):
            self.generateStackedBarChart(handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues);            
        else:
            self.generateBarChart(handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues);

    def generateBarChart(self, handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues):
        numColumns = len(keyFieldValues)
        barWidth = min(0.35, 0.9/len(valueFields))
        x_intv = np.arange(numColumns)
        for i, valueField in enumerate(valueFields):
            ax.bar(x_intv+(i*barWidth), valueFieldValues[i], barWidth, color=colormap(1.*i/numColumns), alpha=0.5, label=valueField)
        plt.xticks(x_intv,keyFieldLabels)
        plt.xlabel(", ".join(keyFields), fontsize=18)

    def generateStackedBarChart(self, handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues):
        numColumns = len(keyFieldValues)
        barWidth = 0.35
        x_intv = np.arange(numColumns)
        ax.bar(x_intv, valueFieldValues[0], barWidth, alpha=0.5, label=valueFields[0])
        colors= ['#79c36a','#f1595f','#599ad3','#f9a65a','#9e66ab','#cd7058','#d77fb3','#727272']
        bottom=valueFieldValues[0]
        for i in range(1,len(valueFields)):
            plt.bar(x_intv,valueFieldValues[i],barWidth,label=valueFields[i],color=colors[i],bottom=bottom)          
            bottom = self.sumzip(bottom,valueFieldValues[i])   

    def sumzip(self,x,y):
        return [sum(values) for values in zip(x,y)]