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
from pixiedust.utils.dataFrameAdapter import PandasDataFrameAdapter
import pixiedust.utils.dataFrameMisc as dataFrameMisc
import numpy as np
from pixiedust.utils import Logger

@Logger()
class PandasDataFrameDataHandler(object):
    def __init__(self, options, entity):
        self.options = options
        self.entity = entity

    def getFieldNames(self, expandNested=False):
        return dataFrameMisc.getFieldNames(PandasDataFrameAdapter(self.entity), expandNested)

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

    @property
    def schema(self):
        return PandasDataFrameAdapter(self.entity).schema

    """
        Return a cleaned up Pandas Dataframe that will be used as working input to the chart
    """
    def getWorkingPandasDataFrame(self, xFields, yFields, extraFields=[], aggregation=None, maxRows = 100):
        if xFields is None or len(xFields)==0:
            #swap the yFields with xFields
            xFields = yFields
            yFields = []
            aggregation = None

        extraFields = [a for a in extraFields if a not in xFields and a not in yFields]
        workingDF = self.entity[xFields + extraFields + yFields]

        if aggregation and len(yFields)>0:
            aggMapper = {"SUM":"sum", "AVG": "mean", "MIN": "min", "MAX": "max"}
            aggFn = aggMapper.get(aggregation, "count")
            workingDF = workingDF.groupby(extraFields + xFields).agg(aggFn).reset_index()

        workingDF = workingDF.dropna()
        count = len(workingDF.index)
        if count > maxRows:
            workingDF = workingDF.sample(frac=(float(maxRows) / float(count)),replace=False)
        
        #sort by xFields
        workingDF.sort_values(extraFields + xFields, inplace=True)
        
        return workingDF