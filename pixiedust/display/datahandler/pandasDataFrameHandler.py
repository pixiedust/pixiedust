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
from pixiedust.utils.dataFrameAdapter import PandasDataFrameAdapter
import pixiedust.utils.dataFrameMisc as dataFrameMisc
from datetime import datetime
import pandas as pd
import numpy as np
from pixiedust.utils import Logger
from six import iteritems
from .baseDataHandler import BaseDataHandler
import re

@Logger()
class PandasDataFrameDataHandler(BaseDataHandler):

    def getFieldNames(self, expandNested=False):
        return dataFrameMisc.getFieldNames(PandasDataFrameAdapter(self.entity), expandNested)

    def count(self):
        return len(self.entity.index)

    def isNumericField(self, fieldName):
        for y in self.entity.columns:
            if y == fieldName:
                return self.entity[y].dtype == np.float64 or self.entity[y].dtype == np.int64
        raise ValueError("Column {} does not existing in the dataframe".format(fieldName))

    def isNumericType(self, field):
        return dataFrameMisc.isNumericType(field.dataType)

    def isStringField(self, fieldName):
        return dataFrameMisc.isStringField(PandasDataFrameAdapter(self.entity), fieldName)

    def isStringType(self, field):
        return dataFrameMisc.isStringType(field.dataType)

    def isDateField(self, fieldName):
        return dataFrameMisc.isDateField(PandasDataFrameAdapter(self.entity), fieldName)

    def isDateType(self, field):
        return dataFrameMisc.isDateType(field.dataType)

    @property
    def schema(self):
        return PandasDataFrameAdapter(self.entity).schema

    def add_numerical_column(self):
        """
        Add a dummy numerical column to the underlying dataframe
        """
        self.entity = self.entity.copy()
        self.entity["pd_count"] = 1
        return "pd_count"

    def get_filtered_dataframe(self, filter_options):
        df = self.entity.copy(deep=True)

        if filter_options is not None:
            field = filter_options['field'] if 'field' in filter_options else ''
            constraint = filter_options['constraint'] if 'constraint' in filter_options else ''
            val = filter_options['value'] if 'value' in filter_options else ''
            regex = filter_options['regex'].lower() == "true" if 'regex' in filter_options else False
            casematters = filter_options['case_matter'].lower() == "true" if 'case_matter' in filter_options else False

            if field and val and field in self.getFieldNames():
                if val == 'None':
                    df = df.loc[df[field].isna() if hasattr(df[field], 'isna') else df[field].isnull()]
                elif not self.isNumericField(field):
                    val = val if regex else ".*" + val + ".*"
                    flags = 0 if casematters else re.IGNORECASE
                    df = df[df[field].str.contains(val, flags=flags)]
                elif constraint == "less_than":
                    df = df.loc[df[field] < float(val)]
                elif constraint == "greater_than":
                    df = df.loc[df[field] > float(val)]
                else: # constraint == "equal_to":
                    df = df.loc[df[field] == float(val)]
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

        allFields = self.getFieldNames()
        myFieldsOrdered = []
        if isTableRenderer:
            if len(extraFields) < 1:
                workingDF = filteredDF
            else:
                for f in allFields:
                    if f in extraFields:
                        myFieldsOrdered.append(f)
                workingDF = filteredDF[myFieldsOrdered]
        else:
            extraFields = [a for a in extraFields if a not in xFields and a not in yFields]
            workingDF = filteredDF[xFields + extraFields + yFields]

        if aggregation and len(yFields)>0:
            aggMapper = {"SUM":"sum", "AVG": "mean", "MIN": "min", "MAX": "max"}
            aggFn = aggMapper.get(aggregation, "count")
            workingDF = workingDF.groupby(extraFields + xFields).agg(aggFn).reset_index()

        if not isTableRenderer:
            workingDF = workingDF.dropna()
        count = len(workingDF.index)
        if count > maxRows:
            workingDF = workingDF.sample(n=int(maxRows),replace=False)

        #check if the caller want to preserve some columns
        preserveCols = self.options.get("preserveCols", None)
        if preserveCols is not None:
            preserveCols = [a for a in preserveCols.split(",") if a not in xFields and a not in yFields]
            cols = { key:[] for key in preserveCols}
            for i in workingDF.index:
                cond = None
                for j, key in enumerate(extraFields + xFields):
                    thisKey = self.entity.loc[i][key]
                    cond = (self.entity[key] == thisKey) if j is 0 else (cond & (self.entity[key] == thisKey))
                p = self.entity[ cond ]
                for key in preserveCols:
                    cols[key].append( p[key].values.tolist()[0] )
            for key, value in iteritems(cols):
                workingDF.insert(len(workingDF.columns), key, value)

        #check if the user wants timeseries
        if len(xFields) == 1 and self.options.get("timeseries", 'false') == 'true':
            field = xFields[0]
            try:
                inputDateFormat = self.options.get("inputDateFormat", None)
                if inputDateFormat is not None:
                    workingDF[field] = workingDF[field].apply(lambda x: datetime.strptime(str(x), inputDateFormat))
                else:
                    workingDF[field] = pd.to_datetime(workingDF[field])
            except:
                self.exception("Unable to convert field {} to datetime".format(field))
        
        if not isTableRenderer:
            #sort by xFields
            workingDF.sort_values(extraFields + xFields, inplace=True)
        
        return workingDF