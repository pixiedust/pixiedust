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
from .plugins.dialog import DialogPlugin
import matplotlib as mpl
import matplotlib.pyplot as plt
import mpld3
import mpld3.plugins as plugins
from random import randint

class LineChartDisplay(ChartDisplay):

    def getDialogOptions(self, handlerId):
        return list('1','2','3')

    def doRender(self, handlerId):
        allNumericCols = self.getNumericalFieldNames()
        if len(allNumericCols) == 0:
            self._addHTML("Unable to find a numerical column in the dataframe")
            return

        # init
        mpld3.enable_notebook()
        fig, ax = plt.subplots()
        plugins.connect(fig, DialogPlugin(handlerId, self.getPrefix(), self._getExecutePythonDisplayScript(), allNumericCols, self.options))
        
        #
        displayCols = []
        selectedCol = self.options.get("col")
        if (selectedCol and selectedCol is not "ALL"):
            displayCols.append(selectedCol)
        else:
            displayCols = allNumericCols

        # plot
        MAX_ROWS = 100
        numRows = min(MAX_ROWS,self.entity.count())
        numCols = len(displayCols)
        pdf = self.entity.toPandas()
        for i, displayCol in enumerate(displayCols):
            xs = list(range(0, numRows))
            ys = pdf[displayCol].tolist()
            ax.plot(xs, ys, label=displayCol)

        # display
        ax.grid(color='lightgray', alpha=0.7)
        ax.legend(title='')        
        
    def getNumericalFieldNames(self):
        schema = self.entity.schema
        fieldNames = []
        for field in schema.fields:
            type = field.dataType.__class__.__name__
            if ( type =="LongType" or type == "IntegerType" ):
                fieldNames.append(field.name)
        return fieldNames