{%extends "executePythonDisplayScript.js"%}

{%block preRunCommandScript%}
var addValueToCommand = function(name, value) {
    if (value) {
        var startIndex, endIndex;
        startIndex = command.indexOf(","+name+"=");
        if (startIndex >= 0) {
            commaIndex = command.indexOf(",", startIndex+1);
            quoteIndex = command.indexOf("'", startIndex+1);
            if (quoteIndex >=0 && quoteIndex < commaIndex) {
                // value is enclosed in quotes - end of value will be second quote
                endIndex = command.indexOf("'", quoteIndex+1) + 1;
            }
            else if (commaIndex >= 0) {
                // end of value is the comma
                endIndex = commaIndex;
            }
            else {
                // no quote or comma found - end of value is at the very end
                endIndex = command.indexOf(")", startIndex+1);
            }
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
        startIndex = command.indexOf(","+name+"=");
        if (startIndex >= 0) {
            commaIndex = command.indexOf(",", startIndex+1);
            quoteIndex = command.indexOf("'", startIndex+1);
            if (quoteIndex >=0 && quoteIndex < commaIndex) {
                // value is enclosed in quotes - end of value will be second quote
                endIndex = command.indexOf("'", quoteIndex+1) + 1;
            }
            else if (commaIndex >= 0) {
                // end of value is the comma
                endIndex = commaIndex;
            }
            else {
                // no quote or comma found - end of value is at the very end
                endIndex = command.indexOf(")", startIndex+1);
            }
            var start = command.substring(0,startIndex);
            var end = command.substring(endIndex);
            command = start + end;
        }
    }
};
var getListValues = function(listId) {
    var value = '';
    $(listId + ' li').each(function(idx, li) {
        if (value.length != 0) {
            value += ',';
        }
        value += $(li).text();
    });
    return value;
};
addValueToCommand('keyFields',getListValues('#keyFields{{prefix}}'));
addValueToCommand('valueFields',getListValues('#valueFields{{prefix}}'));
$('#chartOptions{{prefix}} *').filter(':input').each(function(){
    if ($(this).is(':checkbox')) {
        addValueToCommand($(this).attr('name'),$(this).is(':checked')+'');	
    }
    else {
        addValueToCommand($(this).attr('name'),$(this).val());
    }
});
$('#chartOptions{{prefix}} *').filter('select').each(function(){
    addValueToCommand($(this).attr('name'),$(this).val());
});
{%endblock%}