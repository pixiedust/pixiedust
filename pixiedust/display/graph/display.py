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
        
        if ( handlerId == "forceGraph"):
            import json
            ar = g.edges.select("src","dst").map(lambda (s,d): (s,[d]))\
                .reduceByKey(lambda d1,d2: d1+d2).map(lambda (src, arTargets): (src, list(set(arTargets))))\
                .collect()

            dic = {item[0] : item[1] for item in ar}
            def expand(values, visited,level):
                results=[]
                if values is not None and level < 5:
                    for v in values:
                        if v not in visited and len(results)<level*5:
                            visited[v]=True
                            results.append({ "name": str(v), "children": {}})
                    for item in results:
                        nextVisited = {}
                        nextVisited.update(visited)
                        item["children"]=expand(dic.get(item["name"]), nextVisited, level+1)
                return results

            res = { "name": str(ar[0][0]), "children":expand(dic[ar[0][0]], {ar[0][0]:True}, 1)}
            tree = json.dumps(res)
            self._addScriptElement("https://d3js.org/d3.v3.js", checkJSVar="d3",
                callback=self.renderTemplate("nodeLinkGraph.js", root=tree))
            self._addHTMLTemplateString("""
                <style>
                    .node circle {
                        fill: #fff;
                        stroke: steelblue;
                        stroke-width: 1.5px;
                    }

                    .node {
                        font: 10px sans-serif;
                    }

                    .link {
                        fill: none;
                        stroke: #ccc;
                        stroke-width: 1.5px;
                    }
                </style>
                <svg width="960" height="600"></svg>                
            """)
        else:
            graphNodesJson="{"
            for r in g.vertices.map(lambda row: """"{0}":{{"id":"{0}","name":"{1}","latitude":{2},"longitude":{3}}}"""
                .format(row.id, row.name.encode("ascii","ignore"),0.0 if row.latitude is None else row.latitude,0.0 if row.longitude is None else row.longitude)).collect():
                graphNodesJson+=("," if len(graphNodesJson)>1 else "") + str(r)
            graphNodesJson+="}"        
            graphLinksJson=str(g.edges.select("src","dst").groupBy("src","dst").agg(F.count("src").alias("count")).toJSON().map(lambda j: yaml.safe_load(j)).collect())
    
            self._addScriptElement("https://mbostock.github.io/d3/talk/20111116/d3/d3.js", checkJSVar="d3")
            self._addScriptElement("https://mbostock.github.io/d3/talk/20111116/d3/d3.geo.js")
            self._addScriptElement(
                "https://mbostock.github.io/d3/talk/20111116/d3/d3.geom.js", 
                callback= self.renderTemplate("graphMap.js", graphNodesJson=graphNodesJson, graphLinksJson=graphLinksJson)
            )        
            self._addHTMLTemplate("graphMap.html")
