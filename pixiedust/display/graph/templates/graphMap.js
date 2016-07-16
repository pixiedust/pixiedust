var True=true;
var False=false;
var graph = {"nodes": {{graphNodesJson}},"links":{{graphLinksJson}}};
var prefix = '{{prefix}}';
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