{%import "commonExecuteCallback.js" as commons%}
$('#selectRoot{{prefix}}').click(function() {
    executeNewRoot{{prefix}}(
        $('#root{{prefix}}').val()
    );
});

function executeNewRoot{{prefix}}(rootId){
    var extraCommandOptions = {'root':rootId};
    extraCommandOptions.limitLevel=parseInt($('#limitLevel{{prefix}}').val(),10);
    extraCommandOptions.limitChildren=parseInt($('#limitChildren{{prefix}}').val(),10);
    {% call(results) commons.ipython_execute(this._genDisplayScript(),prefix,extraCommandOptions="extraCommandOptions") %}
        {%if results["error"]%}
            $('#error{{prefix}}').css("display", "block").html({{results["error"]}});
            $("#svg{{prefix}}").css("display","none");
        {%else%}
            d3.select("#svg{{prefix}}").selectAll("*").remove();
            $('#error{{prefix}}').css("display", "block").html("");
            renderTree{{prefix}}(JSON.parse({{results}}));
        {%endif%}
    {% endcall %}
}

var renderTree{{prefix}} = function( root ){
    var diameter = 960;
    var tree = d3.layout.tree()
        .size([360, diameter / 2 - 120])
        .separation(function(a, b) { return (a.parent == b.parent ? 1 : 2) / a.depth; });

    var diagonal = d3.svg.diagonal.radial().projection(function(d) { return [d.y, d.x / 180 * Math.PI]; });

    var svg = d3.select("#svg{{prefix}}")
        .attr("width", diameter)
        .attr("height", diameter)
        .append("g")
        .attr("transform", "translate(" + diameter / 2 + "," + diameter / 2 + ")");

    var nodes = tree.nodes(root),
        links = tree.links(nodes);

    var link = svg.selectAll(".link")
        .data(links)
    .enter().append("path")
        .attr("class", "link")
        .attr("d", diagonal);

    var node = svg.selectAll(".node")
        .data(nodes)
        .enter().append("g")
        .attr("class", "node")
        .attr("transform", function(d) { return "rotate(" + (d.x - 90) + ")translate(" + d.y + ")"; })

    node.append("circle")
        .attr("r", 4.5)
        .style("cursor", function(d){ if (d.children && d.children.length > 0 ){ return "pointer"}})
        .style("fill", function(d){ if (d.children && d.children.length > 0 ){ return "blue"} })
        .on("click", function(d){
            if (d.children && d.children.length > 0 ){
                executeNewRoot{{prefix}}(d.name); 
                $('#root{{prefix}}').val(d.name)
            }
        })
        .on("mouseover", function(d) { if (d.children && d.children.length > 0 ){d3.select(this).style("fill", "red");}})
        .on("mouseout", function(d) {d3.select(this).style("fill", "blue");})

    node.append("text")
        .attr("dy", ".31em")
        .attr("text-anchor", function(d) { return d.x < 180 ? "start" : "end"; })
        .attr("transform", function(d) { return d.x < 180 ? "translate(8)" : "rotate(180)translate(-8)"; })
        .text(function(d) { return d.name; });

    d3.select(self.frameElement).style("height", diameter - 150 + "px");
}

renderTree{{prefix}}({{root}});