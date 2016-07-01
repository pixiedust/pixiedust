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
from pyspark.sql import DataFrame
    
class TableDisplay(Display):
    def doRender(self, handlerId):
        entity=self.entity
        clazz = entity.__class__.__name__        
        if( clazz == "GraphFrame"):
            if handlerId == "edges":
                entity=entity.edges
            else:
                entity=entity.vertices
        if isinstance(entity, DataFrame):
            self.renderDataFrame(entity)
            return
            
        self._addHTML("""
            <b>Unable to display object</b>
        """
        )
        
    def renderDataFrame(self,entity):
        schema = entity.schema
        self._addHTML("""<table class="table table-striped"><thead>""")                   
        for field in schema.fields:
            self._addHTML("<th>" + field.name + "</th>")
        self._addHTML("</thead>")
        self._addHTML("<tbody>")
        for row in entity.take(100):
            self._addHTML("<tr>")
            for field in schema.fields:
                self._addHTML("<td>" + self._safeString(row[field.name]) + "</td>")
            self._addHTML("</tr>")
        self._addHTML("</tbody>")
        self._addHTML("</table>")
        
        
