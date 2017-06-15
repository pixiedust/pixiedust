var True=true;
var False=false;
var graph = {"nodes": {{graphNodesJson}},"links":{{graphLinksJson}}};
var prefix = '{{prefix}}';

var margin = {top: 20, right: 20, bottom: 20, left: 20};
var w = ({{preferredWidth}} - margin.left - margin.right);
var h = ({{preferredHeight}} - margin.top - margin.bottom);

var linksByOrigin = {};
var countByAirport = {};
var locationByAirport = {};
var positions = [];

var d3_geo_radians = Math.PI / 180;
d3.geo.azimuthal = function() {
  var mode = "orthographic", // or stereographic, gnomonic, equidistant or equalarea
      origin,
      scale = 200,
      translate = [480, 250],
      x0,
      y0,
      cy0,
      sy0;

  function azimuthal(coordinates) {
    var x1 = coordinates[0] * d3_geo_radians - x0,
        y1 = coordinates[1] * d3_geo_radians,
        cx1 = Math.cos(x1),
        sx1 = Math.sin(x1),
        cy1 = Math.cos(y1),
        sy1 = Math.sin(y1),
        cc = mode !== "orthographic" ? sy0 * sy1 + cy0 * cy1 * cx1 : null,
        c,
        k = mode === "stereographic" ? 1 / (1 + cc)
          : mode === "gnomonic" ? 1 / cc
          : mode === "equidistant" ? (c = Math.acos(cc), c ? c / Math.sin(c) : 0)
          : mode === "equalarea" ? Math.sqrt(2 / (1 + cc))
          : 1,
        x = k * cy1 * sx1,
        y = k * (sy0 * cy1 * cx1 - cy0 * sy1);
    return [
      scale * x + translate[0],
      scale * y + translate[1]
    ];
  }

  azimuthal.invert = function(coordinates) {
    var x = (coordinates[0] - translate[0]) / scale,
        y = (coordinates[1] - translate[1]) / scale,
        p = Math.sqrt(x * x + y * y),
        c = mode === "stereographic" ? 2 * Math.atan(p)
          : mode === "gnomonic" ? Math.atan(p)
          : mode === "equidistant" ? p
          : mode === "equalarea" ? 2 * Math.asin(.5 * p)
          : Math.asin(p),
        sc = Math.sin(c),
        cc = Math.cos(c);
    return [
      (x0 + Math.atan2(x * sc, p * cy0 * cc + y * sy0 * sc)) / d3_geo_radians,
      Math.asin(cc * sy0 - (p ? (y * sc * cy0) / p : 0)) / d3_geo_radians
    ];
  };

  azimuthal.mode = function(x) {
    if (!arguments.length) return mode;
    mode = x + "";
    return azimuthal;
  };

  azimuthal.origin = function(x) {
    if (!arguments.length) return origin;
    origin = x;
    x0 = origin[0] * d3_geo_radians;
    y0 = origin[1] * d3_geo_radians;
    cy0 = Math.cos(y0);
    sy0 = Math.sin(y0);
    return azimuthal;
  };

  azimuthal.scale = function(x) {
    if (!arguments.length) return scale;
    scale = +x;
    return azimuthal;
  };

  azimuthal.translate = function(x) {
    if (!arguments.length) return translate;
    translate = [+x[0], +x[1]];
    return azimuthal;
  };

  return azimuthal.origin([0, 0]);
};

var projection = d3.geo.azimuthal()
    .mode("equidistant")
    .origin([-98, 38])
    .scale(w)
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