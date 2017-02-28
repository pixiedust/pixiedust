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
        executeDisplay:function(displayCallback){
            displayCallback = displayCallback || {};
            displayCallback.options = displayCallback.options || {};
            function onDisplayDone{{prefix}}(){
                if (displayCallback.onDisplayDone){
                    displayCallback.onDisplayDone();
                }
            }
            var $targetDivId = displayCallback.targetDivId;
            {% call display.executeDisplay(divId="$targetDivId") %}
                addOptions( displayCallback.options );
            {% endcall %}
        },

        {# 
            executeScript helper method: run an arbitray python script
            executeControl:{
                onError(error): callback function called when an error occurs during execution
                onSuccess(results): callback function called when the script has successfully executed
                targetDivId: id of div that will get the spinner
            }
        #}
        executeScript: function(script, executeControl){
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
    }
})();