$("#menu{{prefix}}{{jobId}} [id^=status{{prefix}}]").each(function(){
    if ($(this).text() == "Not Started"){
        $(this).text("Skipped");
    }
})

var n = $("#pm_overallProgress{{prefix}}");
n.attr("value", parseInt(n.attr("max")))