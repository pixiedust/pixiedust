function incProgress(id){
    var n = $(id);
    n.attr("value", parseInt( n.attr("value")) + {{increment}});
}
incProgress("#progress{{prefix}}{{data["stageId"]}}");
incProgress("#pm_overallProgress{{prefix}}");
$("#progressNumTask{{prefix}}{{data["stageId"]}}").text("{{data["taskInfo"]["index"]+1}}");