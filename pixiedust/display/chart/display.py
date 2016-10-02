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

from ..display import Display
from pyspark.sql import functions as F
import pixiedust.utils.dataFrameMisc as dataFrameMisc
    
class ChartDisplay(Display):
    def __init__(self, options, entity):
        super(ChartDisplay,self).__init__(options,entity)
        #note: since this class can be subclassed from other module, we need to mark the correct resource module with resModule so there is no mixup
        self.extraTemplateArgs["resModule"]=ChartDisplay.__module__

    def doRender(self, handlerId):
        self._addHTML("""
            <p><b>Sorry, but this visualization is not yet implemented. Please check back often!</b></p>
        """
        )

    # numerical used as a boolean flag for truth table
    def sampleColumn(self, numerical):
        default=None
        for field in self.entity.schema.fields:
            # Ignore unique ids
            if field.name.lower() != 'id' and ( not numerical or dataFrameMisc.isNumericType(field.dataType) ):
            # Find a good column to display in pie ChartDisplay
                default = default or field.name
                count = self.entity.count()
                sample = self.entity.sample(False, (float(200) / count)) if count > 200 else self.entity
                orderedSample = sample.groupBy(field.name).agg(F.count(field.name).alias("agg")).orderBy(F.desc("agg")).select("agg")
                if orderedSample.take(1)[0]["agg"] > 10:
                    return [field.name]
        # Otherwise, return first non-id column
        return [default]