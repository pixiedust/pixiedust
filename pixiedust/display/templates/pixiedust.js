{%import "executePythonDisplayMacro.js" as display with context%}
{%import "commonExecuteCallback.js" as commons with context%}
var pixiedust = (function(){
    return {
        getCell: function(cell_id){
            {% if gateway %}
            var cells = [];
            {% else %}
            var cells=IPython.notebook.get_cells().filter(function(cell){
                return cell.cell_id==cell_id;
            });
            {%endif%}
            return cells.length>0?cells[0]:null;
        },
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
            user_controls = user_controls || {"options":{}};
            if (user_controls.inFlight){
                console.log("Ignoring request to execute Display that is already being executed");
                return;
            }
            user_controls.inFlight = true;
            var options = $.extend({}, pd_controls.options || {}, user_controls.options || {} );
            function wrapDisplayDone(fn){
                return function(targetNode){
                    user_controls.inFlight = false;
                    if (fn){
                        fn.apply(this);
                    }
                    $(document).trigger('pd_event', {type:"pd_load", targetNode: targetNode});
                }
            }
            user_controls.onDisplayDone = wrapDisplayDone( user_controls.onDisplayDone);
            var pd_prefix = pd_controls.prefix;
            var $targetDivId = user_controls.targetDivId;
            {%include "pd_executeDisplay.js"%}
        },
        executeInDialog:function(pd_controls, user_controls){
            pd_controls = pd_controls || {};
            user_controls = user_controls || {"options":{}};
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
                var dialogRoot = "dialog" + pd_controls.prefix + "root";
                var options = {
                    title: "PixieDust: " + (displayOptions.title || "Dialog"),
                    body: '<div id="' + dialogRoot + '" pixiedust="' + attr_pd_ctrl + '" class="pixiedust"></div>',
                    sanitize:false,
                    notebook: IPython.notebook,
                    keyboard_manager: IPython.notebook.keyboard_manager,
                    maximize_modal: (displayOptions.maximize === "true"),
                    custom_class: (displayOptions.customClass || ''),
                    hide_header: (displayOptions.hideHeader === 'true'),
                    buttons: {
                        OK: {
                            class : "btn-primary btn-ok",
                            click: function() {
                                var dlg = $("#" + dialogRoot + " > pd_dialog");
                                try{
                                    return new Function('global', 'modal_obj', dlg.find("> pd_ok").text().trim())(global, modal_obj);
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

                function resizeDialog() {
                    global.modalBodyStyle = $('.pixiedust .modal-body').attr('style');
                    global.modalFooterStyle = $('.pixiedust .modal-footer').attr('style');
                    $('.pixiedust .modal-body').attr('style', global.modalBodyStyle ? global.modalBodyStyle + ';padding:5px 20px !important;' : 'padding:5px 20px !important;');
                    $('.pixiedust .modal-footer').attr('style', 'display:none !important;');
                    if (options.hide_header) {
                        global.modalHeaderStyle = $('.pixiedust .modal-header').attr('style');
                        $('.pixiedust .modal-header').attr('style', 'display:none !important;');
                    }
                };

                function resetDialog() {
                    if (global.modalBodyStyle) {
                        $('.pixiedust .modal-body').attr('style', global.modalBodyStyle);
                    } else {
                        $('.pixiedust .modal-body').removeAttr('style');
                    }
                    if (global.modalFooterStyle) {
                        $('.pixiedust .modal-footer').attr('style', global.modalFooterStyle);
                    } else {
                        $('.pixiedust .modal-footer').removeAttr('style');
                    }
                    if (global.modalHeaderStyle) {
                        $('.pixiedust .modal-header').attr('style', global.modalHeaderStyle);
                    } else {
                        $('.pixiedust .modal-header').removeAttr('style');
                    }
                };

                var modal_obj = modal(options);
                modal_obj.addClass('pixiedust pixiedust-app ' + options.custom_class);
                if (options.maximize_modal) {
                    modal_obj.addClass('pixiedust pixiedust-app pixiedust-maximize ' + options.custom_class);
                }
                modal_obj.on('shown.bs.modal', function(){
                    resizeDialog();
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
                    user_controls.options.targetDivId = user_controls.targetDivId = dialogRoot;
                    if ( user_controls.options.dialog == 'true'){
                        user_controls.onDisplayDone = function(){
                            var dlg = $("#" + dialogRoot + " > pd_dialog")
                            try{
                                new Function('global', 'modal_obj', dlg.find("> pd_onload").text().trim())(global, modal_obj);
                            }catch(e){
                                console.error(e);
                            }
                        }
                    }
                    pixiedust.dialogRoot = dialogRoot;
                    pixiedust.executeDisplay(pd_controls, user_controls);
                });
                modal_obj.on("hidden.bs.modal", function () {
                    resetDialog();
                    if ( global.KMEnableProto ){
                        var KeyboardManager = require('notebook/js/keyboardmanager').KeyboardManager;
                        KeyboardManager.prototype.enable = global.KMEnableProto;
                        delete global.KMEnableProto;
                    }
                    pixiedust.dialogRoot = null;
                });
            })
        },
        saveOutputInCell: function(curCell, content, html, msg_type){
            if(curCell && curCell.output_area && curCell.output_area.outputs){
                var data = JSON.parse(JSON.stringify(content.data));
                if(!!data["text/html"])data["text/html"]=html;
                function savedData(data){
                    {#hide the output when displayed with nbviewer on github, use the is-viewer-good class which is only available on github#}
                    var markup='<style type="text/css">.pd_warning{display:none;}</style>';
                    markup+='<div class="pd_warning"><em>Hey, there\'s something awesome here! To see it, open this notebook outside GitHub, in a viewer like Jupyter</em></div>';
                    nodes = $.parseHTML(data["text/html"], null, true);
                    var s = $(nodes).wrap("<div>").parent().find(".pd_save").not(".pd_save .pd_save");
                    s.each(function(){
                        var found = false;
                        if ( $(this).attr("id") ){
                            var n = $("#" + $(this).attr("id"));
                            if (n.length>0){
                                found=true;
                                n.each(function(){
                                    $(this).addClass("is-viewer-good");
                                });
                                markup+=n.wrap("<div>").parent().html();
                            }
                        }else{
                            $(this).addClass("is-viewer-good");
                        }
                        if (!found){
                            markup+=$(this).parent().html();
                        }
                    });
                    data["text/html"] = markup;
                    return data;
                }
                curCell.output_area.outputs = [{
                    "data": savedData(data),"metadata":content.metadata,"output_type":msg_type
                }];
            }
        }
    }
})();

function resolveScriptMacros(script){
    script = script && script.replace(/\$val\(\"?(\w*)\"?\)/g, function(a,b){
        var n = $("#" + b );
        var v = null;
        if (n.length > 0){
            if (n.is(':checkbox')){
                v = n.is(':checked').toString();
            }else{
                v = $("#" + b ).val() || $("#" + b ).text();
            }
        }
        if (!v && v!=="" && window[b] && typeof window[b] === "function"){
            v = window[b]();
        }
        if (!v && v!=="" && pixiedust[b] && typeof pixiedust[b] === "function"){
            v = pixiedust[b]();
        }
        if (!v && v!==""){
            console.log("Warning: Unable to resolve value for element ", b);
            return a;
        }
        if (typeof v === "object"){
            return JSON.stringify(v)
                .split('\\').join('\\\\')
                .split("'''").join("\\'\\'\\'")
                .split('"""').join('\\"\\"\\"')
        }
        return v.split('"').join('&quot;').split('\n').join('\\n');
    });
    return script;
}

function getParentScript(element){
    var scripts = [];
    {#Get all parent scripts#}
    $(element).parents("[pd_script]").each(function(){
        scripts.unshift(this.getAttribute("pd_script"));
    });

    {#merge#}
    var script = "";
    $.each( scripts, function(index, value){
        if (value){
            script += "\n" + value;
        }
    });
    return script;
}

function preRun(element){
    var preRunCode = null;
    $(element).find("> pd_script").each(function(){
        var type = this.getAttribute("type");
        if (type=="preRun"){
            preRunCode = $(this).text();
        }
    });
    if (!preRunCode ){
        return true;
    }
    return new Function(preRunCode.trim())();
}

function addOptions(command, options, override=true){
    function getStringRep(v) {
        if (typeof v === 'string' || v instanceof String){
            v = v.replace(/'/g,"\\\'");
        }
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
        }else if (hasValue && command.search(/display\s*\(/) >= 0 ){
            var n = command.lastIndexOf(")");
            command = [command.slice(0, n), (command[n-1]=="("? "":",") + replaceValue, command.slice(n)].join('')
        }        
    }
    return command;
}

function computeGeometry(element, execInfo){
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
}

function readScriptAttribute(element){
    retValue = element.getAttribute("pd_script");
    if (!retValue){
        $(element).find("> pd_script").each(function(){
            var type = this.getAttribute("type");
            if (!type || type=="python"){
                retValue = $(this).text();
            }
        })
    }
    return retValue;
}

function getAttribute(element, name, defValue, defValueIfKeyAlone){
    if (!element.hasAttribute(name)){
        return defValue;
    }
    retValue = element.getAttribute(name);
    return retValue || defValueIfKeyAlone;
}

function readExecInfo(pd_controls, element, searchParents, fromExecInfo){
    if (searchParents === null || searchParents === undefined ){
        searchParents = !element.hasAttribute("pd_stop_propagation");
    }
    var execInfo = {"options":{}};
    $.extend(execInfo, fromExecInfo || {});
    var hasOptions = false;
    $.each( element.attributes, function(){
        if (this.name.startsWith("option_")){
            hasOptions = true;
            execInfo.options[this.name.replace("option_", "")] = this.value || null;
        }
    });
    var pd_options = resolveScriptMacros(element.getAttribute("pd_options"));
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
    {#read pd_options children using json format#}
    $(element).find("> pd_options").each(function(){
        try{
            var options = JSON.parse($(this).text());
            hasOptions = true;
            for (var key in options) { 
                execInfo.options[key] = resolveScriptMacros(options[key]); 
            }
        }catch(e){
            console.log("Error parsing pd_options, invalid json", e);
        }
    })
    execInfo.options.nostore_figureOnly = true;
    execInfo.options.targetDivId = execInfo.targetDivId = pd_controls.refreshTarget || element.getAttribute("pd_target");
    if (execInfo.options.targetDivId){
        execInfo.options.no_margin=true;
    }

    execInfo.options.widget = element.getAttribute("pd_widget");
    execInfo.pixieapp = element.getAttribute("pd_app");
    if (execInfo.pixieapp && !execInfo.targetDivId){
        execInfo.options.targetDivId = execInfo.targetDivId = $(element).uniqueId().attr('id');
    }

    computeGeometry(element, execInfo);

    scriptAttr = readScriptAttribute(element);
    if (scriptAttr){
        execInfo.script = (execInfo.script || "") + "\n" + scriptAttr;
    }
    execInfo.refresh = execInfo.refresh || (getAttribute(element, "pd_refresh", "false", "true")=='true');
    execInfo.norefresh = element.hasAttribute("pd_norefresh");
    execInfo.entity = element.hasAttribute("pd_entity") ? element.getAttribute("pd_entity") || "pixieapp_entity" : null;

    function applyEntity(c, e, doptions){
        {#add pixieapp info #}
        var match = c.match(/display\((\w*),/);
        if (match){
            doptions.nostore_pixieapp = match[1];
        }

        pd_controls.sniffers = pd_controls.sniffers || [];
        pd_controls.sniffers.forEach(function(sniffer){
            c = addOptions(c, eval('(' + sniffer + ')'))       
        });
        if (!e){
            return addOptions(c, doptions);
        }
        c = c.replace(/\((\w*),/, "($1." + e + ",")
        return addOptions(c, doptions);
    }

    if ( (!hasOptions && (execInfo.refresh || execInfo.options.widget) && !execInfo.script) 
        || (!execInfo.script && execInfo.pixieapp)){
        execInfo.script = "#refresh";
    }

    var dialog = (execInfo.options.dialog == "true");
    if ( dialog ){
        execInfo.script = execInfo.script || "#refresh";
        execInfo.refresh = true;
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
                resolveScriptMacros( getParentScript(element) ) + '\n' +
                resolveScriptMacros(execInfo.script);
            if ( execInfo.pixieapp){
                var locOptions = execInfo.options;
                locOptions.cell_id = pd_controls.options.cell_id;
                function makePythonStringOrNone(s){
                    return !s?"None":('"""' + s + '"""')
                }
                function getCellMetadata(){
                    var cell = pixiedust.getCell(execInfo.options.cell_id);
                    var retValue = cell?cell._metadata:{};
                    return JSON.stringify(retValue || {});
                }
                execInfo.script += "\nfrom pixiedust.display.app.pixieapp import runPixieApp" + 
                    "\ntrue=True\nfalse=False\nnull=None" +
                    "\nrunPixieApp('" + 
                    execInfo.pixieapp + "', options=" + JSON.stringify(locOptions) 
                    + ",parent_command=" + makePythonStringOrNone(pd_controls.command)
                    + ",parent_pixieapp=" + makePythonStringOrNone(pd_controls.options.nostore_pixieapp)
                    + ",cell_metadata=" + getCellMetadata()
                    + ")";
            }else if ( ( hasOptions || execInfo.refresh || execInfo.entity || execInfo.options.widget) && 
                    !execInfo.norefresh && $(element).children("target[pd_target]").length == 0){
                {#include a refresh of the whole screen#}
                execInfo.script += "\n" + applyEntity(pd_controls.command, execInfo.entity, execInfo.options)
            }else{
                {#make sure we have a targetDivId#}
                execInfo.targetDivId=execInfo.targetDivId || "pixiedust_dummy";
            }
        }else{
            console.log("Unable to extract entity variable from command", pd_controls.command);
        }
    }

    if (!hasOptions && !execInfo.targetDivId && !execInfo.script){
        if (!searchParents){
            return null;
        }
        return element.hasAttribute("pixiedust")?null:readExecInfo(pd_controls, element.parentElement);
    }

    if (!execInfo.script){
        execInfo.script = applyEntity(pd_controls.command, execInfo.entity, execInfo.options);
    }

    {#pixieapps never write their metadata on the cell #}
    execInfo.nostoreMedatadata = true;

    {#Adjust the targetDivId if in a dialog#}
    if ( pixiedust.dialogRoot ){
        execInfo.targetDivId = execInfo.targetDivId || pixiedust.dialogRoot;
    }

    execInfo.execute = function(){
        {#check if we have a pre-run client side script #}
        if (!preRun(element)){
            return;
        }

        pd_controls.sniffers = pd_controls.sniffers || [];
        pd_controls.sniffers.forEach(function(sniffer){
            if (this.script){
                this.script = addOptions(this.script, eval('(' + sniffer + ')'));
            }else{
                pd_controls.command = addOptions(pd_controls.command, eval('(' + sniffer + ')'));
            }    
        }.bind(this));

        if ( this.options.dialog == 'true' ){
            pixiedust.executeInDialog(pd_controls, this);
        }else{
            pixiedust.executeDisplay(pd_controls, this);
        }
    }

    {#special case pd_refresh points to another element #}
    var refreshTarget = element.getAttribute("pd_refresh");
    if (refreshTarget){
        debugger;
        var retQueue = [execInfo];
        var targets = refreshTarget.split(",");
        $.each( targets, function(index){
            var node = $("#" + this);
            if (node.length){
                pd_controls.refreshTarget = this;
                var thisexecInfo = {"options":{}};
                thisexecInfo.options.targetDivId = this;
                retQueue.push( readExecInfo(pd_controls, node.get(0), false, thisexecInfo) );
            }
        });
        return retQueue
    }

    console.log("execution info: ", execInfo);
    return execInfo;
}

function runElement(element, searchParents){
    var pd_controls = element.getAttribute("pixiedust");
    if (!pd_controls){
        $(element).parents("[pixiedust]").each(function(){
            pd_controls = pd_controls || this.getAttribute("pixiedust");
        });
    }
    var execQueue = [];
    function addToQueue(execInfo){
        if (Array.isArray(execInfo)){
            execInfo.forEach(function(exec){
                execQueue.push(exec);
            });
        }else{
            execQueue.push(execInfo);
        }
    }
    if (pd_controls){
        pd_controls = JSON.parse(pd_controls);
        {#read the current element#}
        addToQueue( readExecInfo(pd_controls, element, searchParents) );

        {#get other execution targets if any#}
        $(element).children("target[pd_target]").each(function(){
            addToQueue( readExecInfo(pd_controls, this, searchParents))
        });
    }
    return execQueue;
}

function filterNonTargetElements(element){
    if (element && ["I", "DIV"].includes(element.tagName)){
        if (!element.hasAttribute("pd_options") || $(element).find("> pd_options").length == 0 || element.hasAttribute("pd_render_onload")){
            return filterNonTargetElements(element.parentElement);
        }
    }
    return element;
}

{#Dynamically add click handler on the pixiedust chrome menus#}
function processEvent(event){
    execQueue = runElement(filterNonTargetElements(event.target));
    {#execute#}
    $.each( execQueue, function(index, value){
        if (value){
            event.stopImmediatePropagation();
            value.execute();
        }
    });
}
$(document).on( "click", "[pixiedust]", function(event){
    if (event.target.tagName == "SELECT" || 
        (event.target.tagName == "INPUT" && (getAttribute(event.target, "type", "").toLowerCase() != "button")) || 
        $(event.target).is(':checkbox')){
        return;
    }
    processEvent(event)
});

$(document).on( "change", "[pixiedust]", function(event){
    processEvent(event)
});

{#handler for customer pd_event#}
$(document).on("pd_event", function(event, eventInfo){
    targetDivId = eventInfo.targetDivId;
    if (targetDivId){
        eventHandlers = $("pd_event_handler").filter(function(){
            if (this.getAttribute("pd_origin") == targetDivId){
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
                    value.execute();
                }
            });
        });
    }else if ( eventInfo.type == "pd_load" && eventInfo.targetNode){
        var execQueue = []
        function accept(element){
            return element.hasAttribute("pd_widget") || element.hasAttribute("pd_render_onload") || element.hasAttribute("pd_refresh_rate");
        }
        eventInfo.targetNode.find("div").each(function(){
            if (accept(this)){
                var thisId = $(this).uniqueId().attr('id');
                this.setAttribute( "id", thisId );
                if (!this.hasAttribute("pd_target") ){
                    this.setAttribute("pd_target", this.getAttribute("id") );
                }
                thisQueue = runElement(this, false);
                var loadingDiv = this;
                $.each( thisQueue, function(index, value){
                    if (value){
                        value.partialUpdate = true;
                        execQueue.push( value );
                        refreshRate = loadingDiv.getAttribute("pd_refresh_rate");
                        if (refreshRate){
                            var ival = setInterval(function(){
                                if ($('#' + thisId).length == 0){
                                    console.log("Clearing refresh timer", ival);
                                    clearInterval(ival);
                                    return;
                                }
                                value.execute();
                            }, parseInt( refreshRate) );
                        }
                    }
                })
            }
        });

        {#execute#}
        $.each( execQueue, function(index, value){
            value.execute();
        });
    }
    else{
        if ( eventInfo.type != "pd_load"){
            console.log("Warning: got a pd_event with no targetDivId", eventInfo);
        }
    }
});