{%import "commonExecuteCallback.js" as commons%}

var validateFields{{prefix}} = function() {
  var msg = ''
  var level = $('#maxDepth{{prefix}}').val()

  if (isNaN(level) || Number(level) < 1) {
    msg = 'Enter a valid value for Max Depth (i.e., number greater than 0)'
  } else {
    var children = $('#maxChildren{{prefix}}').val()
    if (isNaN(children) || Number(children) < 1) {
      msg = 'Enter a valid value for Max Children (i.e., number greater than 0)'
    }
  }

  $('#error{{prefix}}').text(msg)
  
  return !msg
}

var executeTreeUpdate{{prefix}} = function() {
  if (validateFields{{prefix}}()) {
    var extraCommandOptions = {'root': $('#root{{prefix}}').val()}
    extraCommandOptions.maxDepth = parseInt($('#maxDepth{{prefix}}').val())
    extraCommandOptions.maxChildren = parseInt($('#maxChildren{{prefix}}').val())

    {% call(results) commons.ipython_execute(this._genDisplayScript(),prefix,extraCommandOptions="extraCommandOptions") %}
      d3.select("#svg{{prefix}}").selectAll("*").remove()
      {%if results["error"]%}
        $('#error{{prefix}}').txt({{results["error"]}})
      {%else%}
        renderTree{{prefix}}(JSON.parse({{results}}))
      {%endif%}
    {% endcall %}
  }
}

// updated version of: https://gist.github.com/HermanSontrop/8228664
var renderTree{{prefix}} = function (treedata) {
  // console.log("renderTree{{prefix}}:", JSON.stringify(root))

  var margin = {top: 20, right: 20, bottom: 20, left: 20};
  var width = {{preferredWidth}};
  var height = {{preferredHeight}};
      
  var i = 0;
  var duration = 350;
  var root = treedata;

  var tree = d3.layout.tree()
    .size([(width - margin.left - margin.right), (height - margin.top - margin.bottom)])
    .separation(function(a, b) { return (a.parent == b.parent ? 1 : 10) / a.depth; });

  var diagonal = d3.svg.diagonal.radial().projection(function(d) { return [d.y, d.x / 180 * Math.PI]; });

  var svg = d3.select("#svg{{prefix}}")
    .attr("width", width)
    .attr("height", height)
    .append("g")
      .attr("transform", "translate(" + (width - margin.left - margin.right) / 2 + "," + (height - margin.top - margin.bottom) / 2 + ")");
  
  root.x0 = height / 2;
  root.y0 = 0;

  // collapse all children
  // root.children.forEach(collapse);

  update(root);

  d3.select(self.frameElement).style("height", ((height - margin.top - margin.bottom) + "px"));

  function update(source) {
    var nodes = tree.nodes(root);
    var links = tree.links(nodes);
    
    nodes.forEach(function(d) { d.y = d.depth * 80; });
    
    var node = svg.selectAll("g.node")
      .data(nodes, function(d) { return d.id || (d.id = ++i); });
    
    var nodeEnter = node.enter().append("g")
      .attr("class", "node")
      .on("click", click);
    nodeEnter.append("circle")
      .attr("r", 1e-6)
      .style("fill", function(d) { return d._children ? "lightsteelblue" : "#fff"; });
    nodeEnter.append("text")
      .attr("x", 10)
      .attr("dy", ".35em")
      .attr("text-anchor", "start")
      .text(function(d) { return d.name; })
      .style("fill-opacity", 1e-6);

    var nodeUpdate = node.transition()
      .duration(duration)
      .attr("transform", function(d) { return "rotate(" + (d.x - 90) + ")translate(" + d.y + ")"; });
    nodeUpdate.select("circle")
      .attr("r", 4.5)
      .style("fill", function(d) { return d._children ? "lightsteelblue" : "#fff"; });
    nodeUpdate.select("text")
      .style("fill-opacity", 1)
      .attr("transform", function(d) { return d.x < 180 ? "translate(0)" : "rotate(180)translate(-" + (d.name.length + 50)  + ")"; });

    var nodeExit = node.exit().transition()
      .duration(duration)
      .remove();
    nodeExit.select("circle").attr("r", 1e-6);
    nodeExit.select("text").style("fill-opacity", 1e-6);

    var link = svg.selectAll("path.link").data(links, function(d) { return d.target.id; });
    link.enter().insert("path", "g")
      .attr("class", "link")
      .attr("d", function(d) {
        var o = {x: source.x0, y: source.y0};
        return diagonal({source: o, target: o});
      });
    link.transition()
      .duration(duration)
      .attr("d", diagonal);
    link.exit().transition()
      .duration(duration)
      .attr("d", function(d) {
        var o = {x: source.x, y: source.y};
        return diagonal({source: o, target: o});
      })
      .remove();

    nodes.forEach(function(d) {
      d.x0 = d.x;
      d.y0 = d.y;
    });
  }

  function click(d) {
    if (d.children) {
      d._children = d.children;
      d.children = null;
    } else {
      d.children = d._children;
      d._children = null;
    }
    
    update(d);
  }
}

$('#updateGraph{{prefix}}').click(function() {
  executeTreeUpdate{{prefix}}()
})

renderTree{{prefix}}({{tree}});
