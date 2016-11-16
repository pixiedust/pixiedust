var n = $("#progress{{prefix}}{{data["stageId"]}}");
n.attr("value", parseInt( n.attr("value")) + 1);
$("#progressNumTask{{prefix}}{{data["stageId"]}}").text("{{data["taskInfo"]["index"]+1}}")