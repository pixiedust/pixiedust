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

class BaseDataHandler(object):
    def __init__(self, options, entity):
        self.options = options
        self.entity = entity
        self.isStreaming = False

    def add_numerical_column(self):
        raise NotImplementedError()

    def count(self):
        raise NotImplementedError()

    def getFieldNamesAndTypes(self, expandNested=True, sorted=False):
        fieldNames = self.getFieldNames(expandNested)
        fieldNamesAndTypes = []
        for fieldName in fieldNames:
            fieldType = "unknown/unsupported"
            if self.isNumericField(fieldName):
                fieldType = "numeric"
            elif self.isDateField(fieldName):
                fieldType = "date/time"
            elif self.isStringField(fieldName):
                fieldType = "string"
            fieldNamesAndTypes.append((fieldName, fieldType))
        if sorted:
            fieldNamesAndTypes.sort(key=lambda x: str(x[0]))
        return fieldNamesAndTypes

    def get_filtered_dataframe(self, filter_options):
        return self.entity
