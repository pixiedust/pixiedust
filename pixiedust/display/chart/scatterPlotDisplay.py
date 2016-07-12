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
import matplotlib.pyplot as plt
import numpy as np
import warnings
import mpld3
     
class ScatterPlotDisplay(ChartDisplay):
    def doRender(self, handlerId):
        displayColName = self.getNumericalColsInfo()
        if len(displayColName) < 2:
            self._addHTML("Unable to find two numerical columns in the dataframe")
            return
        
        mpld3.enable_notebook()        
        x = self.entity.select(displayColName[0]).toPandas()[displayColName[0]].dropna().tolist()
        y = self.entity.select(displayColName[1]).toPandas()[displayColName[1]].dropna().tolist()

        plt.rcParams['font.size']=11
        plt.rcParams['figure.figsize']=[6.0, 5.0]
        fig, ax=plt.subplots(subplot_kw=dict(axisbg='#EEEEEE'))          
        ax.grid(color='white', linestyle='solid')
        scatter = ax.scatter(x,y,c=y,marker='o',alpha=0.7,s=124,cmap=plt.cm.ocean)
        ax.set_title("D3 Scatter Plot", size=18);
        ax.set_xlabel(displayColName[0], size=14)
        ax.set_ylabel(displayColName[1], size=14)
            
    def getNumericalColsInfo(self):
        schema = self.entity.schema
        fields = []
        for field in schema.fields:
            type = field.dataType.__class__.__name__
            if ( type =="LongType" or type == "IntegerType" ):
                fields = np.append(fields,field.name)
        return fields
