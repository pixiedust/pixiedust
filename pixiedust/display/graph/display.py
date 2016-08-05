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
        
        if ( handlerId == "nodeLinkGraph"):
            import json
            ar = g.edges.select("src","dst").map(lambda (s,d): (s,[d]))\
                .reduceByKey(lambda d1,d2: d1+d2).map(lambda (src, arTargets): (src, list(set(arTargets))))\
                .collect()

            dic = {item[0] : item[1] for item in ar}
            limitLevel = self.options.get("limitLevel", 5)
            limitChildren = self.options.get("limitChildren", 10)
            def expand(values, visited,level):
                results=[]
                if values is not None and level < limitLevel:
                    for v in values:
                        if v not in visited and len(results)<limitChildren:
                            visited[v]=True
                            results.append({ "name": str(v), "children": {}})
                    for item in results:
                        nextVisited = {}
                        nextVisited.update(visited)
                        item["children"]=expand(dic.get(item["name"]), nextVisited, level+1)
                return results
            
            root = self.options.get("root")
            rootNode = ar[0]
            if root:
                def findRoot(ar):
                    for a in ar:
                        if a[0]==root:
                            return a
                rootNode = findRoot(ar)
            
            if not rootNode:
                self._addHTML("<p>Can't find the airport</p>");
                return;

            res = { "name": str(rootNode[0]), "children":expand(dic[ar[0][0]], {rootNode[0]:True}, 1)}
            tree = json.dumps(res)

            #if user specified root, then only send back the json tree
            if root:
                self.addProfilingTime = False
                print(tree)
                return

            self._addScriptElement("https://d3js.org/d3.v3.js", checkJSVar="d3", callback=self.renderTemplate("nodeLinkGraph.js", root=tree))
            self._addHTMLTemplate("nodeLinkGraph.html", root=tree, res=res)
        else:
            graphNodesJson="{"
            for r in g.vertices.map(lambda row: """"{0}":{{"id":"{0}","name":"{1}","latitude":{2},"longitude":{3}}}"""
                .format(row.id, row.name.encode("ascii","ignore"),0.0 if row.latitude is None else row.latitude,0.0 if row.longitude is None else row.longitude)).collect():
                graphNodesJson+=("," if len(graphNodesJson)>1 else "") + str(r)
            graphNodesJson+="}"        
            graphLinksJson=str(g.edges.select("src","dst").groupBy("src","dst").agg(F.count("src").alias("count")).toJSON().map(lambda j: yaml.safe_load(j)).collect())
    
            self._addScriptElement("https://d3js.org/d3.v3.js", checkJSVar="d3")
            self._addScriptElement("https://mbostock.github.io/d3/talk/20111116/d3/d3.geo.js")
            self._addScriptElement(
                "https://mbostock.github.io/d3/talk/20111116/d3/d3.geom.js", 
                callback= self.renderTemplate("graphMap.js", graphNodesJson=graphNodesJson, graphLinksJson=graphLinksJson)
            )        
            self._addHTMLTemplate("graphMap.html")
