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
    extraCommandOptions.colorBy = $('#colorBy{{prefix}}').val()

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
var _graph = null
var renderGraph{{prefix}} = function(graph) {
  if (!graph) {
    graph = _graph
    d3.select("#svg{{prefix}}").selectAll("*").remove()
  }
  if (typeof graph === 'string') {
    graph = JSON.parse(graph)
  }
  _graph = graph

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

  var colorkey = $('#colorBy{{prefix}}').val()
  var cols = d3.map(links, function(d) { return d[colorkey] }).keys()
  var color = cols.length <= 10 ? d3.scale.category10() : d3.scale.category20()

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

  // legend key
  var legendkey = svg.selectAll('rect.legend').data(cols)
  var padding = 5
  var lsize = 15

  // add new keys
  legendkey.enter().append('rect')
    .attr('class', 'legend')
    // .attr('opacity', 0)
    .attr('x', padding)
    .attr('y', function (d, i) { return (i * lsize) + padding })
    .attr('width', lsize - 2)
    .attr('height', lsize - 2)

  // update keys
  legendkey.style('fill', function (d) { return color(d) })

  // remove old keys
  legendkey.exit().transition()
    .attr('opacity', 0)
    .remove()

  // legend label
  // var total = d3.sum(data, function (d) { return d.value })
  var legendlabel = svg.selectAll('text.legend').data(cols)

  // add new labels
  legendlabel.enter().append('text')
    .attr('class', 'legend')
    .attr('x', lsize + 4 + padding)
    .attr('y', function (d, i) { return (i * lsize + 8) + padding })
    .attr('dy', '.25em')

  // update labels
  legendlabel.text(function (d) {
    // var current = data.filter(function (_d) { return _d.key === d })
    // var v = current.length > 0 ? current[0].value : 0
    // return d + ': ' + percent(v / total)
    return d
  })

  // remove old labels
  legendlabel.exit().transition()
    .attr('opacity', 0)
    .remove()
}

$('#updateGraph{{prefix}}').click(function() {
  executeGraphUpdate{{prefix}}()
})

$('#colorBy{{prefix}}').on('change', function() {
  renderGraph{{prefix}}()
})

renderGraph{{prefix}}({{graph}})
