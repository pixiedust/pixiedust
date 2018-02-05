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

from pixiedust.display.chart.renderers import PixiedustRenderer
from pixiedust.utils import Logger
from .brunelBaseDisplay import BrunelBaseDisplay

@PixiedustRenderer(id="lineChart")
@Logger()
class LineChartRenderer(BrunelBaseDisplay):

    def isSubplot(self):
        return self.options.get("lineChartType", None) == "subplots"

    def getExtraFields(self):
        if not self.isSubplot() and len(self.getValueFields())>1:
            #no clusterby if we are grouped and multiValueFields
            return []
    
        clusterby = self.options.get("clusterby")
        return [clusterby] if clusterby is not None else []

    def compute_brunel_magic(self):
        parts = ["line"]
        subplots = self.isSubplot()
        valueFields = self.getValueFields()
        keyFields = self.getKeyFields()
        clusterby = self.options.get("clusterby")
        
        if subplots is False:
            if clusterby is None:
                parts.append("x({})".format(keyFields[0]))
                if len(valueFields) == 1:
                    parts.append("y({})".format(valueFields[0]))
                elif len(valueFields) > 1:
                    parts.append("y({})".format(",".join(valueFields)))
                    parts.append("color(#series)")
            elif clusterby is not None:
                if len(valueFields) > 1:
                    self.addMessage("Warning: 'Cluster By' ignored when grouped option with multiple Value Fields is selected") 
        elif subplots is True:
            if clusterby is None:
                parts.append("x({})".format(keyFields[0]))
                parts.append("y({})".format(valueFields[0]))   
                if len(valueFields) > 1:
                    for panel in range(1,len(valueFields)):
                        parts.append("| line x({})".format(keyFields[0]))
                        parts.append("y({})".format(valueFields[panel]))
            elif clusterby is not None:
                self.addMessage("Warning: 'Cluster By' not implemented for Brunel yet")

        parts.append(self.get_sort())

        return parts
