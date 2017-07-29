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

from ..display import *
from pixiedust.utils.dataFrameAdapter import *
import pixiedust.utils.dataFrameMisc as dataFrameMisc
    
class TableDisplay(Display):
    def doRender(self, handlerId):
        entity=self.entity       
        if dataFrameMisc.fqName(entity) == "graphframes.graphframe.GraphFrame":
            if handlerId == "edges":
                entity=entity.edges
            else:
                entity=entity.vertices
        if dataFrameMisc.isPySparkDataFrame(entity) or dataFrameMisc.isPandasDataFrame(entity):
            self.hideColumns = self.options.get("hideColumns") and [a.strip() for a in self.options.get("hideColumns").split(",")]
            self.showColumns = self.options.get("showColumns") and [a.strip() for a in self.options.get("showColumns").split(",")]
            self._addHTMLTemplate('dataframeTable.html', entity=PandasDataFrameAdapter(entity), table_noschema=self.options.get("table_noschema", "false"))
            return
  
        self._addHTML("""
            <b>Unable to display object {}</b>
        """.format(entity)
        )

    def showField(self, fieldName):
        if self.hideColumns is not None and fieldName in self.hideColumns:
            return False
        if self.showColumns is not None and fieldName not in self.showColumns:
            return False
        return True
