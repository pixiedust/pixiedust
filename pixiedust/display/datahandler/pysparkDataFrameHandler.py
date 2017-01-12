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
import pixiedust.utils.dataFrameMisc as dataFrameMisc
from pyspark.sql import functions as F

class PySparkDataFrameDataHandler(object):
    def __init__(self, options, entity):
        self.options = options
        self.entity = entity

    def __getattr__(self, name):
        if hasattr(self.entity, name):
            return self.entity.__getattribute__(name)
        raise AttributeError("{0} attribute not found".format(name))

    def getFieldNames(self, expandNested=False):
        return dataFrameMisc.getFieldNames(self.entity, expandNested)

    def isNumericField(self, fieldName):
        return dataFrameMisc.isNumericField(self.entity, fieldName)

    def isNumericType(self, field):
        return dataFrameMisc.isNumericType(field.dataType)

    def getFieldValues(self, fieldNames):
        if len(fieldNames) == 0:
            return []
        numericKeyField = False
        if len(keyFields) == 1 and self.isNumericField(fieldNames[0]):
            numericKeyField = True
        df = self.entity.groupBy(fieldNames).count().dropna()
        for fieldName in fieldNames:
            df = df.sort(F.col(fieldName).asc())
        maxRows = int(self.options.get("rowCount","100"))
        numRows = min(maxRows,df.count())
        rows = df.take(numRows)
        values = []
        for i, row in enumerate(rows):
            if numericKeyField:
                values.append(row[fieldNames[0]])
            else:
                values.append(i)
        return values