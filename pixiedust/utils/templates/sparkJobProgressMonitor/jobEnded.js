$("#menu{{prefix}}{{jobId}} [id^=status{{prefix}}]").each(function(){
    if ($(this).text() == "Not Started"){
        $(this).text("Skipped");
    }
})