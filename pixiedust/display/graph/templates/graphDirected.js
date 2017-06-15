{% import "commonExecuteCallback.js" as commons %}

var validateFields{{prefix}} = function() {
  var msg = ''
  var edges = $('#maxEdges{{prefix}}').val()

  if (isNaN(edges) || Number(edges) < 1) {
    msg = 'Enter a valid value for Max Edges (i.e., number greater than 0)'
  }

  $('#error{{prefix}}').text(msg)

  return !msg
}

var executeGraphUpdate{{prefix}} = function() {
  if (validateFields{{prefix}}()) {
    var extraCommandOptions = { 'isupdate': 'true' }
    extraCommandOptions.maxEdges = parseInt($('#maxEdges{{prefix}}').val())

    {% call(results) commons.ipython_execute(this._genDisplayScript(),prefix,extraCommandOptions="extraCommandOptions") %}
      d3.select("#svg{{prefix}}").selectAll("*").remove()
      {%if results["error"]%}
        $('#error{{prefix}}').txt({{results["error"]}})
      {%else%}
        renderGraph{{prefix}}(JSON.parse({{results}}))
      {%endif%}
    {% endcall %}
  }
}

// updated version of: http://bl.ocks.org/d3noob/5141278
var renderGraph{{prefix}} = function(graph) {
  if (typeof graph === 'string') {
    graph = JSON.parse(graph)
  }

  var requiredkeys = ['source', 'src', 'target', 'dst']
  var nodes = {}
  var links = graph.links || graph.edges || graph

  // find the nodes from the edges
  // change 'src', 'dst' to 'source', 'target'
  links.forEach(function(link) {
    link.source = nodes[link.src] ||
      (nodes[link.src] = {name: link.src})
    link.target = nodes[link.dst] ||
      (nodes[link.dst] = {name: link.dst})
  })

  var color = d3.scale.category10()
  var colorkey = null

  var additionalkeys = Object.keys(links[0]).filter(function(k) {
    return requiredkeys.indexOf(k) === -1
  })

  if (additionalkeys && additionalkeys.length > 0) {
    colorkey = additionalkeys[0]
  }

  var margin = {top: 20, right: 20, bottom: 20, left: 20};
  var width = {{preferredWidth}};
  var height = {{preferredHeight}};

  var force = d3.layout.force()
    .nodes(d3.values(nodes))
    .links(links)
    .size([(width - margin.left - margin.right), (height - margin.top - margin.bottom)])
    .linkDistance(Math.min(width, height) / 5)
    .linkStrength(0.2)
    .friction(0.7)
    .charge(-500)
    .on('tick', tick)
    .start()

  var svg = d3.select('#svg{{prefix}}')
    .attr('width', width)
    .attr('height', height)

  // the arrow
  svg.append('svg:defs').selectAll('marker')
      .data(color.range().map(function (c) { return c.replace('#', 'color-') })) // an arrow for each possible color
    .enter().append('svg:marker')
      .attr('id', String)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 15)
      .attr('refY', -1.5)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
    .append('svg:path')
      .attr('d', 'M0,-5L10,0L0,5')
      .style('fill', function (d, i) { return d.replace('color-', '#') })

  // add the edges with arrows
  var path = svg.append('svg:g').selectAll('path')
      .data(force.links())
    .enter().append('svg:path')
      .attr('class', 'link')
      .attr('marker-end', function (d, i) { return 'url(' + color(d[colorkey]).replace('#', '#color-')  + ')' })
      .style('stroke', function (d, i) { return color(d[colorkey]) })

  // the nodes
  var node = svg.selectAll('.node')
      .data(force.nodes())
    .enter().append('g')
      .attr('class', 'node')
      .call(force.drag)

  // add the nodes
  node.append('circle')
      .attr('r', 5)

  // add the node text 
  node.append('text')
      .attr('x', 12)
      .attr('dy', '.35em')
      .text(function(d) { return d.name })

  // update the nodes/edges
  function tick() {
    path.attr('d', function(d) {
      var dx = d.target.x - d.source.x
      var dy = d.target.y - d.source.y
      var dr = Math.sqrt(dx * dx + dy * dy)

      return 'M' + 
        d.source.x + ',' + 
        d.source.y + 'A' + 
        dr + ',' + dr + ' 0 0,1 ' + 
        d.target.x + ',' + 
        d.target.y
    })

    node.attr('transform', function(d) {
      return 'translate(' + d.x + ',' + d.y + ')'
    })
  }
}

$('#updateGraph{{prefix}}').click(function() {
  executeGraphUpdate{{prefix}}()
})

renderGraph{{prefix}}({{graph}})
