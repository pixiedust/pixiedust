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
        },
        executeInDialog:function(pd_controls, user_controls){
            pd_controls = pd_controls || {};
            user_controls = user_controls || {};
            var displayOptions = $.extend({}, pd_controls.options || {}, user_controls.options || {} );
            var global={};
            require(['base/js/dialog'],function(dialog){
                var modal = dialog.modal;
                var attr_pd_ctrl = JSON.stringify(pd_controls).trim()
                    .replace(/&/g, '&amp;')
                    .replace(/'/g, '&apos;')
                    .replace(/"/g, '&quot;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;');
                var options = {
                    title: "Pixiedust: " + (displayOptions.title || "Dialog"),
                    body: '<div id="dialog{{prefix}}root" pixiedust="' + attr_pd_ctrl + '"></div>',
                    sanitize:false,
                    notebook: IPython.notebook,
                    keyboard_manager: IPython.notebook.keyboard_manager,
                    buttons: {
                        OK: {
                            class : "btn-primary btn-ok",
                            click: function() {
                                var dlg = $("#dialog{{prefix}}root > pd_dialog")
                                try{
                                    return new Function('global', 'modal_obj', dlg.find("pd_ok").text().trim())(global, modal_obj);
                                }catch(e){
                                    console.error(e);
                                    return false;
                                }
                            }
                        },
                        Cancel: {
                            class : "btn-cancel",
                            click: function(){
                            }
                        }
                    }
                };
                var modal_obj = modal(options);
                modal_obj.addClass('pixiedust pixiedust-app');
                modal_obj.on('shown.bs.modal', function(){
                    var isFF = navigator.userAgent.toLowerCase().indexOf('firefox') > -1;
                    if( isFF && options.keyboard_manager){
                        {#Only on FF, blur event issue, hard disable keyboard manager#}
                        var KeyboardManager = require('notebook/js/keyboardmanager').KeyboardManager;
                        global.KMEnableProto = KeyboardManager.prototype.enable;
                        KeyboardManager.prototype.enable = function () {
                            this.enabled = false;
                        };
                    }
                    IPython.keyboard_manager.register_events(modal_obj);
                    user_controls.options.targetDivId = user_controls.targetDivId = "dialog{{prefix}}root";
                    user_controls.onDisplayDone = function(){
                        var dlg = $("#dialog{{prefix}}root > pd_dialog")
                        try{
                            new Function('global', 'modal_obj', dlg.find("pd_onload").text().trim())(global, modal_obj);
                        }catch(e){
                            console.error(e);
                        }
                    }
                    pixiedust.executeDisplay(pd_controls, user_controls);
                });
                modal_obj.on("hidden.bs.modal", function () {
                    if ( global.KMEnableProto ){
                        var KeyboardManager = require('notebook/js/keyboardmanager').KeyboardManager;
                        KeyboardManager.prototype.enable = global.KMEnableProto;
                        delete global.KMEnableProto;
                    }
                });
            })
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
    execInfo.options.nostore_figureOnly = true;
    execInfo.options.targetDivId = execInfo.targetDivId = element.getAttribute("pd_target");
    if (execInfo.options.targetDivId){
        execInfo.options.no_margin=true;
    }

    execInfo.options.widget = event.target.getAttribute("pd_widget");

    // unhide parents temporarily to properly calculate width/height
    var parentStyles = [];
    var hiddenBlockStyle = 'visibility: hidden !important; display: block !important;';
    var tDiv = $("#" + execInfo.targetDivId);
    var tDivParents = tDiv.parents().addBack().filter(':hidden');
    tDivParents.each(function() {
        var currentStyle = $(this).attr('style');
        parentStyles.push(currentStyle);
        $(this).attr('style', currentStyle ? currentStyle + ';' + hiddenBlockStyle : hiddenBlockStyle);
    });

    // calculate width/height
    w = tDiv.width()
    if (w) {
        execInfo.options.nostore_cw= w;
    }
    if ($(element).parents(".modal-dialog").length > 0 ) {
        h = tDiv.height()
        if (h) {
            execInfo.options.nostore_ch = h-10;
        }
    }

    // re-hide parents
    tDivParents.each(function(i) {
        if (parentStyles[i] === undefined) {
            $(this).removeAttr('style');
        } else {
            $(this).attr('style', parentStyles[i]);
        }
    });

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

    if (!hasOptions && (execInfo.refresh || execInfo.options.widget) && !execInfo.script){
        execInfo.script = "#refresh";
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
            if ( ( (!execInfo.options.dialog && !execInfo.targetDivId) || execInfo.refresh || execInfo.entity) && $(element).children("target[pd_target]").length == 0){
                {#include a refresh of the whole screen#}
                execInfo.script += "\n" + applyEntity(pd_controls.command, execInfo.entity, execInfo.options)
            }else{
                {#make sure we have a targetDivId#}
                execInfo.targetDivId=execInfo.targetDivId || "dummy";
            }
        }else{
            console.log("Unable to extract entity variable from command", pd_controls.command);
        }
    }

    if (!hasOptions && !execInfo.targetDivId && !execInfo.script){
        return element.hasAttribute("pixiedust")?null:readExecInfo(pd_controls, element.parentElement);
    }

    if (!execInfo.script){
        execInfo.script = applyEntity(pd_controls.command, execInfo.entity, execInfo.options);
    }

    {#pixieapps never write their metadata on the cell #}
    execInfo.nostoreMedatadata = true;

    execInfo.execute = function(){
        if ( this.options.dialog == 'true' ){
            pixiedust.executeInDialog(pd_controls, this);
        }else{
            pixiedust.executeDisplay(pd_controls, this);
        }
    }

    console.log("execution info: ", execInfo);
    return execInfo;
}

function runElement(element){
    var pd_controls = element.getAttribute("pixiedust");
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
            value.execute();
        }
    });
});

$(document).on( "DOMNodeInserted", "[pd_widget]", function(event){
    event.stopImmediatePropagation();
    execQueue = runElement(event.target);
    {#execute#}
    $.each( execQueue, function(index, value){
        if (value){
            value.targetDivId = $(event.target).uniqueId().attr('id');
            $(event.target).removeAttr("pd_widget");
            value.execute();
        }
    });
});

{#handler for customer pd_event#}
$(document).on("pd_event", function(event, eventInfo){
    targetDivId = eventInfo.targetDivId;
    if (targetDivId){
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
            execQueue = runElement(this);
            $.each( execQueue, function(index, value){
                if (value){
                    {#Inject eventInfo#}
                    if (value.script){
                        value.script = "true=True\nfalse=False\neventInfo="+JSON.stringify(eventInfo) + "\n" + value.script;
                    }
                    pixiedust.executeDisplay(pd_controls, value);
                }
            });
        });
    }else{
        console.log("Warning: got a pd_event with no targetDivId", eventInfo);
    }
});