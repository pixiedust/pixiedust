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
            var pd_prefix = options.prefix;
            var $targetDivId = options.targetDivId;
            {%include "pd_executeDisplay.js"%}
            {# call display.executeDisplay(divId="$targetDivId")
                addOptions( user_controls.options || {} );
             endcall #}
        },

        {# 
            executeScript helper method: run an arbitray python script
            executeControl:{
                onError(error): callback function called when an error occurs during execution
                onSuccess(results): callback function called when the script has successfully executed
                targetDivId: id of div that will get the spinner
            }
        
        executeScript: function(pd_prefix, script, executeControl){
            executeControl = executeControl || {};
            var $targetDivId = executeControl.targetDivId;
            var command = script;
            {% call(results) commons.ipython_execute(None,prefix, divId="$targetDivId") %}
                {%if results["message"]%}
                    if (executeControl.onError){
                        executeControl.onError( {{results["message"]}} );
                    }
                {%else%}
                    if (executeControl.onSuccess){
                        executeControl.onSuccess({{results}});
                    }
                {%endif%}
            {% endcall %}            
        }
        #}
    }
})();

function readExecInfo(pd_controls, element){
    var options = {}
    var hasOptions = false;
    $.each( element.attributes, function(){
        if (this.name.startsWith("option_")){
            hasOptions = true;
            options[this.name.replace("option_", "")] = this.value || null;
        }
    });
    var pd_options = element.getAttribute("pd_options");
    if (pd_options){
        var parts = pd_options.split(";");
        $.each( parts, function(){
            var index = this.indexOf("=");
            if ( index > 1){
                hasOptions = true;
                options[this.substring(0, index)] = this.substring(index+1);
            }
        });
    }
    options.targetDivId = element.getAttribute("pd_target");

    options.script = element.getAttribute("pd_script");
    if (!options.script){
        $(element).find("pd_script").each(function(){
            options.script = $(this).text();
            if (options.script){
                options.script = options.script.trim()
                {#set up the self variable#}
                var match = pd_controls.command.match(/display\((\w*),/)
                if (match){
                    var entity = match[1]
                    console.log("Inject self with entity", entity)
                    options.script = "from pixiedust.utils.shellAccess import ShellAccess\n"+
                        "self=ShellAccess['" + entity + "']\n" +
                        options.script;
                }else{
                    console.log("Unable to extract entity variable from command", pd_controls.command);
                }
            }
        })
    }
    if (!hasOptions && !options.$targetDivId && !options.script){
        return null;
    }
    {#pixieapps never write their metadata on the cell #}
    options.nostoreMedatadata = true;

    debugger;
    console.log("execution info: ", options);
    return options;
}

//Dynamically add click handler on the pixiedust chrome menus
$(document).on( "click", "[pixiedust]", function(event){
    event.stopImmediatePropagation();
    pd_controls = event.target.getAttribute("pixiedust");
    if (!pd_controls){
        $(event.target).parents("[pixiedust]").each(function(){
            pd_controls = pd_controls || this.getAttribute("pixiedust");
        });
    }
    if (pd_controls){
        pd_controls = JSON.parse(pd_controls);
        var execQueue = []
        {#read the current element#}
        execQueue.push( readExecInfo(pd_controls, event.target) );

        {#get other execution targets if any#}
        $(event.target).find("[pd_target]").each(function(){
            execQueue.push( readExecInfo(pd_controls, this))
        });

        {#execute#}
        $.each( execQueue, function(index, value){
            if (value){
                pixiedust.executeDisplay(pd_controls, {
                    options: value
                });
            }
        });
    }
} );