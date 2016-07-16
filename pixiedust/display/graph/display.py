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
from pyspark.sql import functions as F
import yaml

class GraphDisplay(Display):
    def doRender(self,handlerId):
        g=self.entity
        graphNodesJson="{"
        for r in g.vertices.map(lambda row: """"{0}":{{"id":"{0}","name":"{1}","latitude":{2},"longitude":{3}}}"""
            .format(row.id, row.name.encode("ascii","ignore"),0.0 if row.latitude is None else row.latitude,0.0 if row.longitude is None else row.longitude)).collect():
            graphNodesJson+=("," if len(graphNodesJson)>1 else "") + str(r)
        graphNodesJson+="}"        
        graphLinksJson=str(g.edges.select("src","dst").groupBy("src","dst").agg(F.count("src").alias("count")).toJSON().map(lambda j: yaml.safe_load(j)).collect())
 
        mainScript = self.renderTemplate("graphMap.js", graphNodesJson=graphNodesJson, graphLinksJson=graphLinksJson)
        self._addScriptElement("https://mbostock.github.io/d3/talk/20111116/d3/d3.js", checkJSVar="d3")
        self._addScriptElement("https://mbostock.github.io/d3/talk/20111116/d3/d3.geo.js")
        self._addScriptElement(
            "https://mbostock.github.io/d3/talk/20111116/d3/d3.geom.js", 
            callback= self.renderTemplate("graphMap.js", graphNodesJson=graphNodesJson, graphLinksJson=graphLinksJson)
        )        
        self._addHTMLTemplate("graphMap.html")
