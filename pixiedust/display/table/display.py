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

from ..display import *
from pyspark.sql import DataFrame
    
class TableDisplay(Display):
    def doRender(self, handlerId):
        entity=self.entity
        clazz = entity.__class__.__name__        
        if fqName(entity) == "graphframes.graphframe.GraphFrame":
            if handlerId == "edges":
                entity=entity.edges
            else:
                entity=entity.vertices
        if isPySparkDataFrame(entity) or isPandasDataFrame(entity):
            self._addHTMLTemplate('dataframeTable.html', entity=entity, dfInfo=DataFrameInfo(entity))
            return
            
        self._addHTML("""
            <b>Unable to display object</b>
        """
        )

class DataFrameInfo(object):
    def __init__(self, entity):
        self.entity = entity
        self.sparkDF = isPySparkDataFrame(entity);

    def count(self):
        if self.sparkDF:
            return self.entity.count()
        else:
            return len(self.entity.index)

    def take(self,num):
        if self.sparkDF:
            return self.entity.take(num)
        else:
            df = self.entity.head(num)
            colNames = self.entity.columns.values.tolist()
            def makeJsonRow(row):
                ret = {}
                for i,v in enumerate(colNames):
                    ret[v]=row[i]
                return ret
            return [makeJsonRow(self.entity.iloc[i].values.tolist()) for i in range(0,len(df.index))]

    def getFields(self):
        if self.sparkDF:
            return self.entity.schema.fields
        else:
            #must be a pandas dataframe
            def createObj(a,b):
                return type("",(),{"jsonValue":lambda self: {"type": b, "name": a}, "name":a})()
            return [createObj(a,b) for a,b in zip(self.entity.columns, self.entity.dtypes)]

    def getTypeName(self):
        if self.sparkDF:
            return self.entity.schema.typeName()
        else:
            return "Pandas DataFrame Row"