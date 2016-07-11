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
from pyspark.sql import functions as F

class BarChartDisplay(ChartDisplay):
    def doRender(self, handlerId):
        displayColName = self.getFirstNumericalColInfo()
        if not displayColName:
            self._addHTML("Unable to find a numerical column in the dataframe")
            return
        
        import mpld3
        #mpld3.enable_notebook()     
        fig = plt.figure()
        
        colLabel = self.getFirstStringColInfo()
        labels =  self.entity.select(colLabel).toPandas()[colLabel].dropna().tolist()
        
        # Label the x and y axis
        plt.xlabel(colLabel, fontsize=18)
        plt.ylabel("average "+displayColName, fontsize=18)
        
       
        
        params = plt.gcf()
        plSize = params.get_size_inches()
        params.set_size_inches( (plSize[0]*2, plSize[1]*2) )

        
        
        #x = self.entity.select(displayColName).toPandas()[displayColName].dropna().tolist()
       
       # Taking average as aggregate for now
        x1 = self.entity.groupBy(displayColName).agg(F.avg(displayColName).alias("avg")).toPandas()
        x = x1["avg"].dropna().tolist()

        x_pos = np.arange(len(x))
        plt.xticks(x_pos,labels)
        plt.bar(x_pos,x,color="blue",alpha=0.5)
        


    def getFirstNumericalColInfo(self):
        # Gets the first numerical column in the dataframe that is of either Long or IntegerType
        schema = self.entity.schema
        for field in schema.fields:
            type = field.dataType.__class__.__name__
            if ( type =="LongType" or type == "IntegerType" ):
                return field.name
   
    def getFirstStringColInfo(self):
        # Gets the first non numerical column in the dataframe 
        schema = self.entity.schema
        for field in schema.fields:
            type = field.dataType.__class__.__name__
            if (type != "LongType" and type != "IntegerType" and field.name.lower() !="id"):
                return field.name