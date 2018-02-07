# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2018
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
from pyspark.sql.functions import lit
from pyspark.sql.types import DecimalType
import time
import pandas as pd
from pixiedust.utils import Logger
from .baseDataHandler import BaseDataHandler

@Logger()
class PySparkDataFrameDataHandler(BaseDataHandler):

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

    def isStringField(self, fieldName):
        return dataFrameMisc.isStringField(self.entity, fieldName)

    def isStringType(self, field):
        return dataFrameMisc.isStringType(field.dataType)

    def isDateField(self, fieldName):
        return dataFrameMisc.isDateField(self.entity, fieldName)

    def isDateType(self, field):
        return dataFrameMisc.isDateType(field.dataType)

    def getFieldValues(self, fieldNames):
        if len(fieldNames) == 0:
            return []
        numericKeyField = False
        if len(fieldNames) == 1 and self.isNumericField(fieldNames[0]):
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

    def add_numerical_column(self):
        """
        Add a dummy numerical column to the underlying dataframe
        """
        self.entity = self.entity.withColumn("pd_count", lit(1))
        return "pd_count"

    def get_filtered_dataframe(self, filter_options):
        df = self.entity
        if filter_options is not None:
            field = filter_options['field'] if 'field' in filter_options else ''
            constraint = filter_options['constraint'] if 'constraint' in filter_options else ''
            val = filter_options['value'] if 'value' in filter_options else ''
            regex = filter_options['regex'].lower() == "true" if 'regex' in filter_options else False
            casematters = filter_options['case_matter'].lower() == "true" if 'case_matter' in filter_options else False

            if field and val and field in self.getFieldNames():
                if not self.isNumericField(field):
                    val = val if regex else ".*" + val + ".*"
                    val = val if casematters else "(?i)" + val
                    df = df.filter(df[field].rlike(val))
                else: # a numeric SQL query
                    c = "=="
                    if constraint == "less_than":
                        c = "<"
                    if constraint == "greater_than":
                        c = ">"
                    df = df.filter(field + " " + c + " " + val)
        return df

    """
        Return a cleaned up Pandas Dataframe that will be used as working input to the chart
    """
    def getWorkingPandasDataFrame(self, xFields, yFields, extraFields=[], aggregation=None, maxRows = 100, filterOptions={}, isTableRenderer=False):
        filteredDF = self.get_filtered_dataframe(filterOptions)

        if xFields is None or len(xFields)==0:
            #swap the yFields with xFields
            xFields = yFields
            yFields = []
            aggregation = None

        if isTableRenderer:
            if len(extraFields) < 1:
                workingDF = filteredDF
            else:
                workingDF = filteredDF.select(extraFields)
        else:
            extraFields = [a for a in extraFields if a not in xFields]
            workingDF = filteredDF.select(xFields + extraFields + yFields)

        if aggregation and len(yFields)>0:
            aggMapper = {"SUM":"sum", "AVG": "avg", "MIN": "min", "MAX": "max"}
            aggregation = aggMapper.get(aggregation, "count")

            workingDF = workingDF.groupBy(extraFields + xFields).agg(dict([(yField, aggregation) for yField in yFields]))            
            for yField in yFields:
                workingDF = workingDF.withColumnRenamed("{0}({1})".format(aggregation,yField), yField)

        if not isTableRenderer:
            workingDF = workingDF.dropna()
        count = workingDF.count()
        if count > maxRows:
            workingDF = workingDF.sample(False, (float(maxRows) / float(count)))
        pdf = self.toPandas(workingDF)

        #check if the user wants timeseries
        if len(xFields) == 1 and self.options.get("timeseries", 'false') == 'true':
            field = xFields[0]
            try:
                pdf[field] = pd.to_datetime(pdf[field])
            except:
                self.exception("Unable to convert field {} to datetime".format(field))

        if not isTableRenderer:
            #sort by xFields
            pdf.sort_values(xFields + extraFields, inplace=True)
        return pdf

    """
    Custom implementation of toPandas. It checks the spark type of each column in the dataframe for DecimalType. If any are found, it checks the 
    corresponding pandas dataframe column to make sure it's not a python object type (which would cause an issue during plotting). If that's the case, 
    it casts them as float
    """
    def toPandas(self, workingDF):        
        decimals = []
        for f in workingDF.schema.fields:
            if f.dataType.__class__ == DecimalType:
                decimals.append(f.name)

        pdf = workingDF.toPandas()
        for y in pdf.columns:
            if pdf[y].dtype.name == "object" and y in decimals:
                #spark converts Decimal type to object during toPandas, cast it as float
                pdf[y] = pdf[y].astype(float)

        return pdf

