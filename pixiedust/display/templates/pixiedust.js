{%import "executePythonDisplayMacro.js" as display with context%}
{%import "commonExecuteCallback.js" as commons with context%}
var pixiedust = (function(){
    return {
        {# 
            executeDisplay helper method: run a new display command
            displayCallback:{
                options: dictionary of new options to add to the display command
                onDisplayDone: callback function called when the display run is done executing
                targetDivId: id of div that will receive the output html, none means the default output
            }
        #}
        executeDisplay:function(pd_controls, user_controls){
            pd_controls = pd_controls || {};
            user_controls = user_controls || {};
            var options = $.extend({}, pd_controls.options || {}, user_controls.options || {} );
            function onDisplayDone(){
                if (user_controls.onDisplayDone){
                    user_controls.onDisplayDone();
                }
            }
            var pd_prefix = pd_controls.prefix;
            var $targetDivId = user_controls.targetDivId;
            {%include "pd_executeDisplay.js"%}
            {# call display.executeDisplay(divId="$targetDivId")
                addOptions( user_controls.options || {} );
             endcall #}
        }
    }
})();

function resolveScriptMacros(script){
    script = script.replace(/\$val\(\"?(\w*)\"?\)/g, function(a,b){
        var v = $("#" + b ).val();
        if (!v){
            console.log("Warning: Unable to resolve value for element ", b);
            return a;
        }
        return "\"" + v + "\"";
    });
    return script;
}

function addOptions(command, options, override=true){
    function getStringRep(v) {
        return "'" + v + "'";
    }
    for (var key in (options||{})){
        var value = options[key];
        var hasValue = value != null && typeof value !== 'undefined' && value !== '';
        var replaceValue = hasValue ? (key+"=" + getStringRep(value) ) : "";
        var pattern = (hasValue?"":",")+"\\s*" + key + "\\s*=\\s*'(\\\\'|[^'])*'";
        var rpattern=new RegExp(pattern);
        var n = command.search(rpattern);
        if ( n >= 0 ){
            if (override){
                command = command.replace(rpattern, replaceValue);
            }
        }else if (hasValue){
            var n = command.lastIndexOf(")");
            command = [command.slice(0, n), (command[n-1]=="("? "":",") + replaceValue, command.slice(n)].join('')
        }        
    }
    return command;
}

function readExecInfo(pd_controls, element){
    var execInfo = {}
    execInfo.options = {}
    var hasOptions = false;
    $.each( element.attributes, function(){
        if (this.name.startsWith("option_")){
            hasOptions = true;
            execInfo.options[this.name.replace("option_", "")] = this.value || null;
        }
    });
    var pd_options = element.getAttribute("pd_options");
    if (pd_options){
        var parts = pd_options.split(";");
        $.each( parts, function(){
            var index = this.indexOf("=");
            if ( index > 1){
                hasOptions = true;
                execInfo.options[this.substring(0, index)] = this.substring(index+1);
            }
        });
    }
    execInfo.options.targetDivId = execInfo.targetDivId = element.getAttribute("pd_target");
    w = $("#" + execInfo.targetDivId).width()
    if (w){
        execInfo.options.nostore_cw= w;
    }

    execInfo.script = element.getAttribute("pd_script");
    if (!execInfo.script){
        $(element).find("pd_script").each(function(){
            execInfo.script = $(this).text();
        })
    }

    execInfo.refresh = element.hasAttribute("pd_refresh");
    execInfo.entity = element.hasAttribute("pd_entity") ? element.getAttribute("pd_entity") || "pixieapp_entity" : null;

    function applyEntity(c, e, doptions){
        if (!e){
            return addOptions(c, doptions);
        }
        c = c.replace(/\((\w*),/, "($1." + e + ",")
        return addOptions(c, doptions);
    }

    if (execInfo.script){
        execInfo.script = execInfo.script.trim()
        {#set up the self variable#}
        var match = pd_controls.command.match(/display\((\w*),/)
        if (match){
            var entity = match[1]
            console.log("Inject self with entity", entity)
            execInfo.script = "from pixiedust.utils.shellAccess import ShellAccess\n"+
                "self=ShellAccess['" + entity + "']\n" +
                resolveScriptMacros(execInfo.script);
            if (!execInfo.targetDivId || execInfo.refresh || execInfo.entity){
                {#include a refresh of the whole screen#}
                execInfo.script += "\n" + applyEntity(pd_controls.command, execInfo.entity, execInfo.options)
            }
        }else{
            console.log("Unable to extract entity variable from command", pd_controls.command);
        }
    }

    if (!hasOptions && !execInfo.targetDivId && !execInfo.script){
        return null;
    }

    if (!execInfo.script){
        execInfo.script = applyEntity(pd_controls.command, execInfo.entity, execInfo.options);
    }

    {#pixieapps never write their metadata on the cell #}
    execInfo.nostoreMedatadata = true;

    console.log("execution info: ", execInfo);
    return execInfo;
}

function runElement(element){
    pd_controls = element.getAttribute("pixiedust");
    if (!pd_controls){
        $(element).parents("[pixiedust]").each(function(){
            pd_controls = pd_controls || this.getAttribute("pixiedust");
        });
    }
    var execQueue = [];
    if (pd_controls){
        pd_controls = JSON.parse(pd_controls);
        {#read the current element#}
        execQueue.push( readExecInfo(pd_controls, element) );

        {#get other execution targets if any#}
        $(element).children("target[pd_target]").each(function(){
            execQueue.push( readExecInfo(pd_controls, this))
        });
    }
    return execQueue;
}

{#Dynamically add click handler on the pixiedust chrome menus#}
$(document).on( "click", "[pixiedust]", function(event){
    execQueue = runElement(event.target);
    {#execute#}
    $.each( execQueue, function(index, value){
        if (value){
            event.stopImmediatePropagation();
            pixiedust.executeDisplay(pd_controls, value);
        }
    });
});

{#handler for customer pd_event#}
$(document).on("pd_event", function(event, eventInfo){
    targetDivId = eventInfo.targetDivId;
    if (targetDivId){
        debugger;
        eventHandlers = $("pd_event_handler").filter(function(){
            if (this.getAttribute("pd_target") == targetDivId){
                return true;
            }
            {#Find a parent with pd_target attribute#}
            return $(this).parents("[pd_target]").filter(function(){
                return this.getAttribute("pd_target") == targetDivId;
            }).length > 0;
        });
        eventHandlers.each(function(){
            debugger;
            execQueue = runElement(this);
            $.each( execQueue, function(index, value){
                if (value){
                    {#Inject eventInfo#}
                    if (value.script){
                        value.script = "eventInfo="+JSON.stringify(eventInfo) + "\n" + value.script;
                    }
                    pixiedust.executeDisplay(pd_controls, value);
                }
            });
        });
    }else{
        console.log("Warning: got a pd_event with no targetDivId", eventInfo);
    }
});