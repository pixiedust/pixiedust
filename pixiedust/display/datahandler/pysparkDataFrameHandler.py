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
import time
from pixiedust.utils import Logger

@Logger()
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

    """
        Return a cleaned up Pandas Dataframe that will be used as working input to the chart
    """
    def getWorkingPandasDataFrame(self, xFields, yFields, extraFields=[], aggregation=None, maxRows = 100):
        if xFields is None or len(xFields)==0:
            #swap the yFields with xFields
            xFields = yFields
            yFields = []
            aggregation = None

        workingDF = self.entity.select(xFields + [a for a in extraFields if a not in xFields] + yFields)
        if aggregation and len(yFields)>0:
            aggMapper = {"SUM":"sum", "AVG": "avg", "MIN": "min", "MAX": "max"}
            aggregation = aggMapper.get(aggregation, "count")

            workingDF = workingDF.groupBy(xFields).agg(dict([(yField, aggregation) for yField in yFields]))            
            for yField in yFields:
                workingDF = workingDF.withColumnRenamed("{0}({1})".format(aggregation,yField), yField)

        workingDF = workingDF.dropna()
        count = workingDF.count()
        if count > maxRows:
            workingDF = workingDF.sample(False, (float(maxRows) / float(count)))
        pdf = workingDF.toPandas()
        #sort by xFields
        pdf.sort_values(xFields, inplace=True)
        return pdf

