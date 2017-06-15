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

from ..display import Display
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
import yaml
import pixiedust
import json

myLogger = pixiedust.getLogger(__name__)

class GraphDisplay(Display):
    def doRender(self,handlerId):
        g = self.entity
        width = int(self.getPreferredOutputWidth() - 10 )
        height = int(self.getPreferredOutputHeight() - 10  )

        if handlerId == "graphMap":
            graphNodesJson="{"

            for r in g.vertices.rdd.map(lambda row: """"{0}":{{"id":"{0}","name":"{1}","latitude":{2},"longitude":{3}}}"""
                .format(row.id, row.name.encode("ascii","ignore").decode("ascii"),0.0 if row.latitude is None else row.latitude,0.0 if row.longitude is None else row.longitude)).collect():
                graphNodesJson+=("," if len(graphNodesJson)>1 else "") + str(r)

            graphNodesJson+="}"

            graphLinksJson = str(g.edges.select("src","dst").groupBy("src","dst").agg(F.count("src").alias("count")).toJSON().map(lambda j: yaml.safe_load(j)).collect())
            
            myLogger.debug("graphMap - nodes: {0}".format(graphNodesJson))
            myLogger.debug("graphMap - links: {0}".format(graphLinksJson))

            self._addScriptElement("https://d3js.org/d3.v3.js", checkJSVar="d3",
                callback=self.renderTemplate("graphMap.js", graphNodesJson=graphNodesJson, graphLinksJson=graphLinksJson, preferredWidth=width, preferredHeight=height))

            self._addHTMLTemplate("graphMap.html")

        elif handlerId == "graphTree":
            def expand(values, visited, level):
                results=[]
                if values is not None and level < maxDepth:
                    for v in values:
                        if v not in visited and len(results)<maxChildren:
                            visited[v]=True
                            results.append({ "name": str(v), "children": {}})
                    for item in results:
                        nextVisited = {}
                        nextVisited.update(visited)
                        item["children"]=expand(dic.get(item["name"]), nextVisited, level+1)
                return results
            
            ar = g.edges.select("src","dst").rdd.map(lambda row: (row[0],[row[1]]))\
                .reduceByKey(lambda d1,d2: d1+d2).map(lambda row: (row[0], list(set(row[1]))))\
                .collect()

            dic = {item[0] : item[1] for item in ar}
            maxDepth = self.options.get("maxDepth", 5)
            maxChildren = self.options.get("maxChildren", 10)
            root = self.options.get("root")
            rootNode = ar[0]

            if root:
                def findRoot(ar):
                    for a in ar:
                        if a[0]==root:
                            return a
                rootNode = findRoot(ar)
            
            if not rootNode:
                self._addHTML("<p>Root node not found!</p>")
            else:
                res = { "name": str(rootNode[0]), "children":expand(dic[ar[0][0]], {rootNode[0]:True}, 1)}
                tree = json.dumps(res)

                myLogger.debug("graphTree - tree: {0}".format(res))

                #if user specified root, then only send back the json tree
                if root:
                    self.addProfilingTime = False
                    print(tree)
                else:
                    nodes = g.vertices.select('id').orderBy('id').rdd.map(lambda r: r[0]).collect()
                    self._addScriptElement("https://d3js.org/d3.v3.js", checkJSVar="d3", 
                        callback=self.renderTemplate("graphTree.js", root=str(rootNode[0]), tree=tree, preferredWidth=width, preferredHeight=height))
                    self._addHTMLTemplate("graph.html", root=str(rootNode[0]), nodes=nodes, maxDepth=maxDepth, maxChildren=maxChildren, handlerId=handlerId)
            
        else:
            # force-directed graph
            maxEdges = self.options.get("maxEdges", 100)
            cols = [g.edges.columns[i] for i in range(len(g.edges.columns)) if g.edges.columns[i] not in ['src', 'dst']]
            edges = g.edges.toPandas()[:maxEdges].to_json(orient='records')
            graph = json.dumps(edges)
            isupdate = self.options.get("isupdate")

            cols.sort()
            colorBy = self.options.get("colorBy", cols[0] if len(cols) > 0 else "")

            myLogger.debug("graphDirected - edges: {0}".format(edges))

            #if user specified update, then only send back the json graph
            if isupdate:
                self.addProfilingTime = False
                print(graph)
            else:
                self._addScriptElement("https://d3js.org/d3.v3.js", checkJSVar="d3",
                    callback=self.renderTemplate("graphDirected.js", graph=graph, preferredWidth=width, preferredHeight=height, colorBy=colorBy))
                self._addHTMLTemplate("graph.html", maxEdges=maxEdges, handlerId=handlerId, cols=cols, colorBy=colorBy)
