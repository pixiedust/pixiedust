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
from pyspark.sql.types import DataType,StructType
from pixiedust.utils import *

"""
return True is entity is a spark DataFrame
"""
def isPySparkDataFrame(entity):
    return fqName(entity)=="pyspark.sql.dataframe.DataFrame"

"""
return True is entity is a Pandas DataFrame
"""
def isPandasDataFrame(entity):
    return fqName(entity)=="pandas.core.frame.DataFrame"

"""
Return a list of field names for the given dataframe
will expand nested structures if expandNested is set to True
"""
def getFieldNames(df, expandNested=False):
    def getFieldName(field, expand):
        if isinstance(field.dataType, StructType) and expand:
            retFields = []
            for f in field.dataType.fields:
                retFields.extend([field.name + "." + name for name in getFieldName(f, expand)])
            return retFields
        else:
            return [field.name]
    fieldNames = []
    for field in df.schema.fields:
        fieldNames.extend( getFieldName(field, expandNested) )
    return fieldNames

"""
Return True if spark type is numeric
"""
def isNumericType(type):
    if isinstance( type, DataType):
        return isNumericType( type.__class__.__name__)
    return (type =="LongType" or type == "IntegerType" or type == "DoubleType" or type == "DecimalType" or type == "FloatType")

"""
Return True is field represented by fieldName is Numeric
"""
def isNumericField(entity, fieldName):
    def isNumericFieldRecurse(field, targetName):
        if field.name == targetName:
            return isNumericType(field.dataType)
        elif isinstance(field.dataType, StructType) and targetName.startswith(field.name + "."):
            nestedFieldName = targetName[len(field.name)+1:]
            for f in field.dataType.fields:
                if isNumericFieldRecurse(f, nestedFieldName):
                    return True         
        return False
    for field in entity.schema.fields:
        if isNumericFieldRecurse(field, fieldName):
            return True
    return False