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

    def compute_brunel_magic(self):
        parts = ["line"]
        subplots = self.isSubplot()
        valueFields = self.getValueFields()
        clusterby = self.options.get("clusterby")
        self.debug("clusterby: {}".format(clusterby))
        self.debug("subplots: {}".format(subplots))
        #self.debug("Fields: {}".format(fieldNames[1]))
        
        for index, key in enumerate(self.getKeyFields()):
            if subplots is False:
                if clusterby is None:
                    parts.append("x({})".format(key))
                    if len(valueFields) == 1:
                        parts.append("y({})".format(valueFields[0]))
                    elif len(valueFields) > 1:
                        parts.append("y({})".format(",".join(valueFields)))
                        parts.append("color(#series)")
                elif clusterby is not None:
                    if len(valueFields) > 1:
                        self.addMessage("Warning: 'Cluster By' ignored when grouped option with multiple Value Fields is selected") 
                    #else:    
                        #for j, valueField in enumerate(valueFields):
                        #    pivot = self.getWorkingPandasDataFrame().pivot(
                        #    index=keyFields[0], columns=clusterby, values=valueField)
                        #    pivot.index.name=keyFields[0]        
            elif subplots is True:
                if clusterby is None:
                    parts.append("x({})".format(key))
                    parts.append("y({})".format(valueFields[0]))   
                    if len(valueFields) > 1:
                         for panel in range(1,len(valueFields)):
                            parts.append("| line x({})".format(key))
                            parts.append("y({})".format(valueFields[panel]))
                elif clusterby is not None:
                    self.addMessage("Warning: 'Cluster By' not implemented for Brunel yet")


                        
                    
        
        # for index, key in enumerate(self.getKeyFields()):
        #     if index > 0:
        #         parts.append("+ line")
        #     parts.append("x({})".format(key))
        #     parts.append("y({})".format(",".join(self.getValueFields())))
        #     fieldNames = self.getValueFields()
        #     if len(fieldNames) > 1:
        #         parts.append("color(#series)")
        #     #elif  
        #     parts.append(self.get_sort())
        parts.append(self.get_sort())

        return parts
