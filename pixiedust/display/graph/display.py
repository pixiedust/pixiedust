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
        prefix=self.getPrefix()

        mainScript = """
            var True=true;
            var False=false;
            var graph = {"nodes": """ + graphNodesJson + ""","links":"""+graphLinksJson+"""};
            var prefix = '""" + prefix + """';
            var w = 1000;
            var h = 600;

            var linksByOrigin = {};
            var countByAirport = {};
            var locationByAirport = {};
            var positions = [];

            var projection = d3.geo.azimuthal()
                .mode("equidistant")
                .origin([-98, 38])
                .scale(1400)
                .translate([w/2, h/2]);

            var path = d3.geo.path().projection(projection);

            var svg = d3.select("#map" + prefix).insert("svg:svg", "h2").attr("width", w).attr("height", h);

            var states = svg.append("svg:g").attr("id", "states")
            var circles = svg.append("svg:g").attr("id", "circles");
            var cells = svg.append("svg:g").attr("id", "cells");
            var arc = d3.geo.greatArc()
                .source(function(d) { return locationByAirport[d.source]; })
                .target(function(d) { return locationByAirport[d.target]; });

            // Draw US map.
            d3.json("https://mbostock.github.io/d3/talk/20111116/us-states.json", function(collection) {
                states.selectAll("path")
                .data(collection.features)
                .enter().append("svg:path")
                    .attr("d", path);
                }
            );

            // Parse links
            graph.links.forEach(function(link) {
                var links = linksByOrigin[link.src] || (linksByOrigin[link.src] = []);
                links.push({ source: link.src, target: link.dst });
                countByAirport[link.src] = (countByAirport[link.src] || 0) + 1;
                countByAirport[link.dst] = (countByAirport[link.dst] || 0) + 1;
            });
                    
            var keys=[]
            for (key in graph.nodes){
                var v = graph.nodes[key];
                var loc=[+v.longitude,+v.latitude];
                locationByAirport[key] = loc;
                positions.push(projection(loc));
                keys.push(v)
            }
                    
            // Compute the Voronoi diagram of airports' projected positions.
            var polygons = d3.geom.voronoi(positions);
            var g = cells.selectAll("g#cells").data(keys).enter().append("svg:g")
            g.append("svg:path")
                .attr("class", "cell")
                .attr("d", function(d, i) { return "M" + (polygons[i]?polygons[i].join("L"):"L") + "Z"; })
                .on("mouseover", function(d, i) { d3.select("#airport" + prefix).text(d.name + "(" + d.id + ")" ); });
                        
            g.selectAll("path.arc")
                .data(function(d) { return linksByOrigin[d.id] || []; })
                .enter().append("svg:path")
                .attr("class", "arc")
                .attr("d", function(d) { return path(arc(d)); });

            circles.selectAll("circle")
                .data(keys)
                .enter().append("svg:circle")
                .attr("class", function(d){ return (linksByOrigin[d.id]?"origin":"")})
                .attr("cx", function(d, i) { return positions[i][0]; })
                .attr("cy", function(d, i) { return positions[i][1]; })
                .attr("r", function(d, i) { return (Math.sqrt(countByAirport[d.id])); })
                .sort(function(a, b) { return (countByAirport[b.id] - countByAirport[a.id]); });
        """
        self._addScriptElement("https://mbostock.github.io/d3/talk/20111116/d3/d3.js", checkJSVar="d3")
        self._addScriptElement("https://mbostock.github.io/d3/talk/20111116/d3/d3.geo.js")
        self._addScriptElement("https://mbostock.github.io/d3/talk/20111116/d3/d3.geom.js", callback=mainScript)        
        self._addHTML("""
            <style type="text/css">
                #states path {
                    fill: #ccc;
                    stroke: #fff;
                }

                path.arc {
                    pointer-events: none;
                    fill: none;
                    stroke: #000;
                    display: none;
                }

                path.cell {
                    fill: none;
                    pointer-events: all;
                }

                circle {
                    fill: steelblue;
                    fill-opacity: .8;
                    stroke: #fff;
                }
                
                .origin {
                    fill: green;
                    fill-opacity: .8;
                    stroke: #fff;
                }

                #cells.voronoi path.cell {
                    stroke: brown;
                }

                #cells g:hover path.arc {
                    display: inherit;
                }
            </style>
            <div id="airport""" + prefix + """"/>
            <div id="map""" + prefix + """"/>
        """)
