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

from .mpld3ChartDisplay import Mpld3ChartDisplay
from pyspark.sql import functions as F
    
class PieChartDisplay(Mpld3ChartDisplay):
    def doRenderMpld3(self, handlerId, figure, axes, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues):
        agg = self.options.get("aggregation", "count")
        displayColName = self.getPieColInfo(agg != "count")
        if not displayColName:
            self._addHTML("Unable to find a suitable column in the dataframe")
            return

        pand = self.handleUIOptions(displayColName)
        x = pand["agg"].dropna().tolist()
        labels=pand[displayColName].tolist()

        # The default startangle is 0. With startangle=90, everything is rotated counter-clockwise by 90 degrees
        axes.pie(x, labels=labels, explode=None, autopct='%1.1f%%', startangle=90)


        # numerical used as a boolean flag for truth table
    def getPieColInfo(self, numerical):
        # If user selects a column in dialog box, give it to them
        keyFields = self.options.get("keyFields")
        if keyFields is not None:
            return keyFields

        schema = self.entity.schema
        default=None
        for field in schema.fields:
            # Ignore unique ids
            if field.name.lower() != 'id' and ( not numerical or isNum(field.dataType.__class__.__name__) ):
            # Find a good column to display in pie ChartDisplay
                default = default or field.name
                count = self.entity.count()
                sample = self.entity.sample(False, (float(200) / count)) if count > 200 else self.entity
                orderedSample = sample.groupBy(field.name).agg(F.count(field.name).alias("agg")).orderBy(F.desc("agg")).select("agg")
                if orderedSample.take(1)[0]["agg"] > 10:
                    return field.name
        # Otherwise, return first non-id column
        return default


        # Handle user-defined aggregate functions
    def handleUIOptions(self, displayColName):
        agg = self.options.get("aggregation")
        valFields = self.options.get("valueFields")

        if agg == 'COUNT':
            return self.entity.groupBy(displayColName).agg(F.count(displayColName).alias("agg")).toPandas()
        elif agg == 'SUM':
            return self.entity.groupBy(displayColName).agg(F.sum(valFields).alias("agg")).toPandas()
        elif agg == 'AVG':
            return self.entity.groupBy(displayColName).agg(F.avg(valFields).alias("agg")).toPandas()
        elif agg == 'MIN':
            return self.entity.groupBy(displayColName).agg(F.min(valFields).alias("agg")).toPandas()
        elif agg == 'MAX':
            return self.entity.groupBy(displayColName).agg(F.max(valFields).alias("agg")).toPandas()
        elif agg == 'MEAN':
            return self.entity.groupBy(displayColName).agg(F.mean(valFields).alias("agg")).toPandas()
        else:
            return self.entity.groupBy(displayColName).agg(F.count(displayColName).alias("agg")).toPandas()


    def isNum(type):
        if ( type =="LongType" or type == "IntegerType" ):
            return true
        else:
            return false