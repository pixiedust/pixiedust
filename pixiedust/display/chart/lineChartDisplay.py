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
import matplotlib as mpl
import matplotlib.pyplot as plt
import mpld3

class LineChartDisplay(ChartDisplay):

    def doRender(self, handlerId):
        colNames = self.getNumericalFieldNames()
        if len(colNames) == 0:
            self._addHTML("Unable to find a numerical column in the dataframe")
            return

        # init
        mpld3.enable_notebook()
        fig, ax = plt.subplots()

        # plot
        MAX_ROWS = 100
        numRows = min(MAX_ROWS,self.entity.count())
        numCols = len(colNames)
        pdf = self.entity.toPandas()
        for i, colName in enumerate(colNames):
            xs = list(range(0, numRows))
            ys = pdf[colName].tolist()
            ax.plot(xs, ys, label=colName)

        # display
        ax.grid(color='lightgray', alpha=0.7)
        ax.legend()
        
    def getNumericalFieldNames(self):
        schema = self.entity.schema
        fieldNames = []
        for field in schema.fields:
            type = field.dataType.__class__.__name__
            if ( type =="LongType" or type == "IntegerType" ):
                fieldNames.append(field.name)
        return fieldNames