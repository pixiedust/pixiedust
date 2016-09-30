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
import numpy as np
import pandas as pd
import re
from pyspark.sql.types import *
import pixiedust.utils.dataFrameMisc as dataFrameMisc

def createDataframeAdapter(entity):
    if dataFrameMisc.isPandasDataFrame(entity):
        return PandasDataFrameAdapter(entity)
    elif dataFrameMisc.isPySparkDataFrame(entity):
        return entity
    raise ValueError("Invalid argument")

"""
Adapter interface to Spark APIs. Passed to pixiedust visualizations that expect a Spark DataFrame so they can work
with pandas dataframe with no code change.

This is Experimental, currently support only a subset of the Spark DataFrame APIs.
"""
class PandasDataFrameAdapter(object):
    def __init__(self, entity):
        self.entity = entity
        self.sparkDF = dataFrameMisc.isPySparkDataFrame(entity);

    def __getattr__(self, name):
        if self.sparkDF and hasattr(self.entity, name):
            return self.entity.__getattribute__(name)
        if name=="schema":
            return type("AdapterSchema",(),{"fields": self.getFields()})()
        elif name=="groupBy":
            return lambda cols: AdapterGroupBy(self.entity.groupby(cols))
        elif name=="dropna":
            return lambda: PandasDataFrameAdapter(pd.DataFrame(self.entity.dropna()))
        elif name=="sort":
            return lambda arg: self
        elif name=="select":
            return lambda name: PandasDataFrameAdapter(self.entity[name].reset_index())
        elif name=="orderBy":
            return lambda col: PandasDataFrameAdapter(self.entity.sort("agg",ascending=False))

        raise AttributeError("{0} attribute not found".format(name))

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
                return type("",(),{
                    "jsonValue":lambda self: {"type": b, "name": a}, "name":a,
                    "dataType": IntegerType() if np.issubdtype(b, np.integer) else StringType()
                })()
            return [createObj(a,b) for a,b in zip(self.entity.columns, self.entity.dtypes)]

    def getTypeName(self):
        if self.sparkDF:
            return self.entity.schema.typeName()
        else:
            return "Pandas DataFrame Row"

    def toPandas(self):
        if self.sparkDF:
            return self.entity.toPandas()
        else:
            return self.entity

class AdapterGroupBy(object):
    def __init__(self, group):
        self.group = group

    def count(self):
        return PandasDataFrameAdapter(self.group.size().reset_index(name="count"))

    def agg(self,exp):
        m=re.search("(\w+?)\((.+?)\)(?:.+?(?:as\s+(\w*))|$)",str(exp),re.IGNORECASE)
        if m is None:
            raise AttributeError("call to agg with not supported expression: {0}".format(str(exp)))
        
        funcName=m.group(1).upper()
        groupedCol=m.group(2)
        alias=m.group(3) or "agg"
        if funcName=="SUM":
            return PandasDataFrameAdapter(self.group[groupedCol].sum().reset_index(name=alias))
        elif funcName=="AVG":
            return PandasDataFrameAdapter(self.group[groupedCol].mean().reset_index(name=alias))
        elif funcName == "MIN":
            return PandasDataFrameAdapter(self.group[groupedCol].min().reset_index(name=alias))
        elif funcName == "MAX":
            return PandasDataFrameAdapter(self.group[groupedCol].max().reset_index(name=alias))
        elif funcName == "COUNT":
            return PandasDataFrameAdapter(self.group[groupedCol].count().reset_index(name=alias))
        else:
            raise AttributeError("Unsupported aggregation function {0}".format(funcName))