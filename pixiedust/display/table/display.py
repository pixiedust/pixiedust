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

    def count(self):
        return self.entity.count()

    def take(self,num):
        return self.entity.take(num)

    def getFields(self):
        if isPySparkDataFrame(self.entity):
            return self.entity.schema.fields
        else:
            #must be a pandas dataframe
            return zip(self.entity.columns, self.entity.dtypes)

    def getTypeName(self):
        if isPySparkDataFrame(self.entity):
            return self.entity.schema.typeName()
        else:
            return "Pandas DataFrame Row"