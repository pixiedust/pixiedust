{%extends "executePythonDisplayScript.js"%}

{%block preRunCommandScript%}
var addValueToCommand = function(name, value) {
    if (value) {
        var startIndex, endIndex;
        startIndex = command.indexOf(","+name+"='");
        if (startIndex >= 0) {
            endIndex = command.indexOf("'", startIndex+1);
            endIndex = command.indexOf("'", endIndex+1) + 1;
        }
        else {
            startIndex = endIndex = command.lastIndexOf(")");
        }
        var start = command.substring(0,startIndex);
        var end = command.substring(endIndex);
        command = start + "," + name +"='" + value + "'" + end;
    }
    else {
        var startIndex, endIndex;
        startIndex = command.indexOf(","+name+"='");
        if (startIndex >= 0) {
            endIndex = command.indexOf("'", startIndex+1);
            endIndex = command.indexOf("'", endIndex+1) + 1;
            var start = command.substring(0,startIndex);
            var end = command.substring(endIndex);
            command = start + end;
        }
    }
}
$('#chartOptions{{prefix}} *').filter(':input').each(function(){
    if ($(this).is(':checkbox')) {
        addValueToCommand($(this).attr('name'),$(this).is(':checked')+"");	
    }
    else {
        addValueToCommand($(this).attr('name'),$(this).val());
    }
});
$('#chartOptions{{prefix}} *').filter('select').each(function(){
    addValueToCommand($(this).attr('name'),$(this).val());
});
{%endblock%}