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
from pixiedust.utils import *
from pixiedust.utils.environment import Environment
from six import PY2

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

def checkIfDataType(type):
    if Environment.hasSpark:
        from pyspark.sql.types import DataType
        return isinstance(type, DataType)
    else:
        return fqName(type).endswith("Type")

"""
Return a list of field names for the given dataframe
will expand nested structures if expandNested is set to True
"""
def getFieldNames(df, expandNested=False):
    def getFieldName(field, expand):
        if fqName(field.dataType) == "pyspark.sql.types.StructType" and expand:
            retFields = []
            for f in field.dataType.fields:
                retFields.extend([field.name + "." + name for name in getFieldName(f, expand)])
            return retFields
        else:
            return [field.name.decode('utf-8') if PY2 else field.name]
    fieldNames = []
    for field in df.schema.fields:
        fieldNames.extend( getFieldName(field, expandNested) )
    return fieldNames

"""
Return True if spark type is numeric
"""
def isNumericType(type):
    if checkIfDataType(type):
        return isNumericType( type.__class__.__name__)
    return (type =="LongType" or type == "IntegerType" or type == "DoubleType" or type == "DecimalType" or type == "FloatType")

"""
Return True if spark type is a string
"""
def isStringType(type):
    if checkIfDataType(type):
        return isStringType( type.__class__.__name__)
    return (type =="StringType")

"""
Return True if spark type is a date
"""
def isDateType(type):
    if checkIfDataType(type):
        return isDateType( type.__class__.__name__)
    return (type =="DateType")

"""
Return True is field represented by fieldName is Numeric
"""
def isNumericField(entity, fieldName):
    def isNumericFieldRecurse(field, targetName):
        if field.name == targetName:
            return isNumericType(field.dataType)
        elif fqName(field.dataType)  == "pyspark.sql.types.StructType" and targetName.startswith(field.name + "."):
            nestedFieldName = targetName[len(field.name)+1:]
            for f in field.dataType.fields:
                if isNumericFieldRecurse(f, nestedFieldName):
                    return True         
        return False
    for field in entity.schema.fields:
        if isNumericFieldRecurse(field, fieldName):
            return True
    return False

"""
Return True is field represented by fieldName is a String
"""
def isStringField(entity, fieldName):
    def isStringFieldRecurse(field, targetName):
        if field.name == targetName:
            return isStringType(field.dataType)
        elif checkIfDataType(field.dataType) and targetName.startswith(field.name + "."):
            nestedFieldName = targetName[len(field.name)+1:]
            for f in field.dataType.fields:
                if isStringFieldRecurse(f, nestedFieldName):
                    return True         
        return False
    for field in entity.schema.fields:
        if isStringFieldRecurse(field, fieldName):
            return True
    return False

"""
Return True is field represented by fieldName is a Date
"""
def isDateField(entity, fieldName):
    def isDateFieldRecurse(field, targetName):
        if field.name == targetName:
            return isDateType(field.dataType)
        elif checkIfDataType(field.dataType) and targetName.startswith(field.name + "."):
            nestedFieldName = targetName[len(field.name)+1:]
            for f in field.dataType.fields:
                if isDateFieldRecurse(f, nestedFieldName):
                    return True         
        return False
    for field in entity.schema.fields:
        if isDateFieldRecurse(field, fieldName):
            return True
    return False