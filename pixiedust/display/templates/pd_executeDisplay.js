!function() {
    function getTargetNodeId(override=null){
        return override || $targetDivId || ("wrapperHTML"+ pd_prefix);
    }
    function getTargetNode(override=null){
        return $('#' + getTargetNodeId(override));
    }
    function checkRootInit(){
        node = getTargetNode();
        var retValue = node.is("[pd_init]");
        if (retValue){
            node.removeAttr("pd_init");
        }
        return retValue;
    }
    function setText(targetNode, contents, pdCtl = null, userCtl = null){
        var pd_elements = []
        targetNode.children().each(function(){
            if (this.tagName.toLowerCase().startsWith("pd_")){
                pd_elements.push($(this).clone());
            }
        });
        if (!targetNode.hasClass("use_stream_output")){
            targetNode.text(contents);
        }else{
            var consoleNode = targetNode.children("div.consoleOutput");
            if (consoleNode.length == 0){
                consoleNode = targetNode.append('<div class="consoleOutput"></div>').children("div.consoleOutput");
            }
            var existing = consoleNode.text();
            if (existing != ""){
                contents = existing + "\n" + contents;
            }
            consoleNode.html('<pre style="max-height: 300px;border: 1px lightgray solid;margin-top: 20px;">' + contents + "</pre>");
        }
        if (pd_elements.length > 0 ){
            targetNode.append(pd_elements);
        }
        return true;
    }
    function setHTML(targetNode, contents, pdCtl = null, userCtl = null){
        var pd_elements = []
        targetNode.children().each(function(){
            var eltName = this.tagName.toLowerCase();
            if (eltName.startsWith("pd_") || (eltName == "div" && this.classList.contains("consoleOutput")) ){
                pd_elements.push($(this).clone());
            }
        });
        targetNode.html("<div pd_stop_propagation style='height:100%;'>" + contents + "</div>");
        if (pd_elements.length > 0 ){
            targetNode.append(pd_elements);
        }
        return true;
    }

    function send_input_reply(cb, cmd, pd_controls){
        if (cmd == 'c' || cmd == 'continue' || cmd == 'q' || cmd == 'quit' || cmd.startsWith("$$")){
            cb = null;
            pixiedust.input_reply_queue.queue = [];
            pixiedust.input_reply_queue.callbacks = {};
            $("#debugger_container_" + pd_controls.prefix).hide();
            if (cmd.startsWith("$$")){
                cmd = cmd.substring(2);
            }
        }else if (cmd == 'no_op'){
            cb = null;
            cmd = null;
        }
        if (cb && $targetDivId == "debugger_refresh"){
            cb.refreshDebugger = true;
        }
        pixiedust.input_reply_queue.inflight = cb;
        if (cmd){
            var prolog = cb ? "print('" + pixiedust.input_reply_queue.registerCallback(cb) + "');;" : "";
            IPython.notebook.session.kernel.send_input_reply( prolog + cmd );
        }
    }
    var cellId = options.cell_id || "";
    var curCell = pixiedust.getCell(cellId);
    console.log("curCell",curCell);
    {#Resend the display command#}
    var callbacks = {
        shell : {
            reply : function(){
                if ( !callbacks.response ){
                    var targetNodeUpdated = false;
                    if (!user_controls.partialUpdate){
                        targetNodeUpdated = setHTML(getTargetNode(), "",pd_controls, user_controls);
                    }
                    if (user_controls.onDisplayDone){
                        user_controls.onDisplayDone(getTargetNode(), targetNodeUpdated);
                    }
                }
            },
            payload : {
                set_next_input : function(payload){
                    if (curCell){
                        curCell._handle_set_next_input(payload);
                    }
                }
            }
        },
        iopub:{
            output:function(msg){
                if (curCell && !$targetDivId && getTargetNode().length == 0){
                    curCell.output_area.handle_output.apply(curCell.output_area, arguments);
                    return;
                }
                callbacks.response = true;
                console.log("msg", msg);
                {% if not gateway %}
                if (cellId == ""){
                    if (curCell){
                        curCell.output_area.handle_output.apply(curCell.output_area, arguments);
                        curCell.output_area.outputs=[];
                    }else{
                        console.log("Could not find current cell");
                    }
                    return;
                }
                {% endif %}
                var msg_type=msg.header.msg_type;
                var content = msg.content;
                var targetNodeUpdated = false;
                if(msg_type==="stream"){
                    var reply_callbacks = pixiedust.input_reply_queue.parseCallback(content);
                    if (reply_callbacks && reply_callbacks != callbacks){
                        if (reply_callbacks.iopub){
                            reply_callbacks.iopub.output(msg);
                        }
                        return;
                    }
                    var useHTML = false;
                    var process_output = getScriptOfType($("#" + $targetDivId), "process_output");
                    if (process_output){
                        try{
                            content.text = new Function('output', process_output)(content.text);
                            useHTML = true;
                        }catch(e){
                            console.log("Error while invoking post output function", e, content.text, process_output);
                        }
                    }
                    if (user_controls.onSuccess){
                        user_controls.onSuccess(content.text);
                    }else{
                        fn = useHTML?setHTML:setText;
                        targetNodeUpdated = fn(getTargetNode(), content.text, pd_controls, user_controls);
                    }
                }else if (msg_type==="display_data" || msg_type==="execute_result"){
                    var html=null;
                    if (!!content.data["text/html"]){
                        html=content.data["text/html"];
                    }else if (!!content.data["image/png"]){
                        html=html||"";
                        html+="<img src='data:image/png;base64," +content.data["image/png"]+"'></img>";
                    }
                                                    
                    if (!!content.data["application/javascript"]){
                        try {
                            eval(content.data["application/javascript"]);
                        } catch(err) {
                            curCell.output_area.handle_output.apply(curCell.output_area, arguments);
                        }                        
                        return;
                    }
                    
                    if (html){
                        try{
                            if (user_controls.onSuccess){
                                user_controls.onSuccess(html);
                            }else{
                                targetNodeUpdated = setHTML(getTargetNode(), html, pd_controls, user_controls);
                            }
                            if (content.metadata && content.metadata.pixieapp_metadata){
                                {% if gateway %}
                                var groups = []
                                for (var key in content.metadata.pixieapp_metadata) {
                                    groups.push(key + "=" + content.metadata.pixieapp_metadata[key]);
                                }
                                var query = groups.join("&")
                                if (query){
                                    var queryPos = window.location.href.indexOf("?");
                                    newUrl = "?" + query;
                                    if (queryPos > 0){
                                        var existingQuery = window.location.href.substring(queryPos+1);
                                        var args = existingQuery.split("&");
                                        {#Keep only the token argument#}
                                        for (i in args){
                                            var parts = args[i].split("=");
                                            if (parts.length > 1 && parts[0] == "token"){
                                                newUrl += "&token=" + parts[1];
                                            }
                                        }
                                    }
                                    window.history.pushState("PixieApp", "", newUrl);
                                }
                                {%else%}
                                if (curCell){
                                    curCell._metadata.pixiedust.pixieapp = content.metadata.pixieapp_metadata;
                                }
                                {%endif%}
                            }                            
                        }catch(e){
                            console.log("Invalid html output", e, html);
                            targetNodeUpdated = setHTML(getTargetNode(),  "Invalid html output: " + e.message + "<pre>" 
                                + html.replace(/>/g,'&gt;').replace(/</g,'&lt;').replace(/"/g,'&quot;') + "<pre>",
                                pd_controls, user_controls);
                        }
                        if (callbacks.options && callbacks.options.nostore_delaysave){
                            setTimeout(function(){
                                pixiedust.saveOutputInCell(curCell, content, html, msg_type);
                            }, 1000);
                        }else{
                            pixiedust.saveOutputInCell(curCell, content, html, msg_type);
                        }
                    }
                }else if (msg_type === "error") {
                    {% if gateway %}
                    targetNodeUpdated = setHTML(getTargetNode(), content.traceback, pd_controls, user_controls);
                    {%else%}
                    require(['base/js/utils'], function(utils) {
                        if (content.ename == "BdbQuit"){
                            targetNodeUpdated = setHTML(
                                getTargetNode(), 
                                "PixieDebugger exited", 
                                pd_controls, 
                                user_controls
                            );
                        }else{
                            var tb = content.traceback;
                            console.log("tb",tb);
                            if (tb && tb.length>0){
                                var data = tb.reduce(function(res, frame){return res+frame+'\\n';},"");
                                console.log("data",data);
                                data = utils.fixConsole(data);
                                data = utils.fixCarriageReturn(data);
                                data = utils.autoLinkUrls(data);
                                if (user_controls.onError){
                                    user_controls.onError(data);
                                }else{
                                    var debugger_html = '<button type="submit" pd_options="new_parent_prefix=false" pd_target="' + 
                                    getTargetNodeId() + '" pd_app="pixiedust.apps.debugger.PixieDebugger">Post Mortem</button>' +
                                    '<span>&nbsp;&nbsp;</span>' +
                                    '<button type="submit" pd_options="new_parent_prefix=false;debug_route=true" pd_target="' + 
                                    getTargetNodeId() + '" pd_app="pixiedust.apps.debugger.PixieDebugger">Debug Route</button>'

                                    targetNodeUpdated = setHTML(
                                        getTargetNode(), 
                                        debugger_html + "<pre>" + data + '</pre>' + debugger_html, 
                                        pd_controls, 
                                        user_controls
                                    );
                                }
                            }
                        }
                    });
                    {%endif%}
                }else{
                    callbacks.response = false;
                }
                if (user_controls.onDisplayDone){
                    user_controls.onDisplayDone(getTargetNode(), targetNodeUpdated);
                }
            }
        },
        input : function(msg){
            var reply_callbacks = pixiedust.input_reply_queue.inflight;
            if (!reply_callbacks || reply_callbacks.refreshDebugger){
                $("#debugger_container_" + pd_controls.prefix).show();
                var input_target = "input_reply_" + pd_controls.prefix;
                var process_output = getScriptOfType($("#" + input_target), "process_output");
                if (process_output){
                    try{
                        if (reply_callbacks){
                            reply_callbacks.refreshDebugger = false;
                        }
                        if (!pixiedust.input_reply_queue.inflight){
                            pixiedust.input_reply_queue.inflight = {};
                        }
                        msg.content.prompt = new Function('output', process_output)(msg.content.prompt);
                        targetNodeUpdated = setHTML(getTargetNode(input_target), msg.content.prompt, pd_controls, user_controls);
                        if (user_controls.onDisplayDone){
                            user_controls.onDisplayDone(getTargetNode(input_target), targetNodeUpdated);
                        }
                    }catch(e){
                        console.log("Error while invoking post output function", e, msg.content.prompt, process_output);
                    }
                }else{
                    console.log("No element with id input_reply_"+pd_controls.prefix + " found");
                }
            }
            if (reply_callbacks && reply_callbacks.answer_input_reply){
                var answer = reply_callbacks.answer_input_reply;
                reply_callbacks.answer_input_reply = null;
                send_input_reply(reply_callbacks, answer, pd_controls);
            }else{
                var next_input_reply = pixiedust.input_reply_queue.queue.shift();
                if (next_input_reply && next_input_reply.command == "no_op_delay"){
                    next_input_reply = pixiedust.input_reply_queue.queue.shift();
                }
                if (next_input_reply){
                    send_input_reply(next_input_reply.callbacks, next_input_reply.command, pd_controls);
                }else{
                    pixiedust.input_reply_queue.inflight = null;
                }
            }
            console.log("Handling input msg request: ", msg);
        }
    }
    {% if gateway %}
    if(true){
    {% else %}
    if (IPython && IPython.notebook && IPython.notebook.session && IPython.notebook.session.kernel){
    {% endif %}
        var command = user_controls.script || pd_controls.command.replace("cellId",cellId);
        if ( !user_controls.script){
            function addOptions(options, override=true, ignoreKeys=[]){
                function getStringRep(v) {
                    return "'" + v + "'";
                }
                for (var key in (options||{})){
                    if (ignoreKeys.indexOf(key)>=0){
                        continue;
                    }
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
            }
            if(typeof cellMetadata != "undefined" && cellMetadata.displayParams){
                addOptions(cellMetadata.displayParams);
                addOptions({"showchrome":"true"});
            }else if (curCell && curCell._metadata.pixiedust ){
                if (!pd_controls.avoidMetadata){
                    ignoreKeys = pd_controls.options.nostore_pixieapp?["handlerId"]:[];
                    if (pd_controls.override_keys){
                        Array.prototype.push.apply(ignoreKeys,pd_controls.override_keys);
                    }
                    pd_controls.include_keys || []
                    addOptions(curCell._metadata.pixiedust.displayParams || {}, pd_controls.useCellMetadata, ignoreKeys);
                }else{
                    {#always include new fields and the one in include_keys#}
                    var includeKeys = pd_controls.include_keys || [];
                    var includeOptions = {};
                    for (var key in (curCell._metadata.pixiedust.displayParams||{})){
                        if (includeKeys.indexOf(key) > -1 || !(key in pd_controls.options)){
                            includeOptions[key] = curCell._metadata.pixiedust.displayParams[key];
                        }
                    }
                    addOptions(includeOptions);
                }
            }
            addOptions(user_controls.options||{});
            var pattern = "\\w*\\s*=\\s*'(\\\\'|[^'])*'";
            var rpattern=new RegExp(pattern,"g");
            var n = command.match(rpattern);
            {#find the org_params if any#}
            var org_params = {}
            for (var i=0; i<n.length;i++){
                var parts = n[i].split("=")
                if (parts[0].trim() == "org_params"){
                    var value = parts[1].trim()
                    var values = value.substring(1,value.length-1).split(",");
                    for (var p in values){
                        org_params[values[p].trim()] = true;
                    }
                    break;
                }
            }
            var displayParams={}
            for (var i = 0; i < n.length; i++){
                var parts=n[i].split("=");
                var key = parts[0].trim();
                var value = parts[1].trim()
                if (!key.startsWith("nostore_") && key != "showchrome" && key != "prefix" && key != "cell_id" && key != "org_params" && !!!org_params[key]){
                    displayParams[key] = value.substring(1,value.length-1);
                }
            }

            {% if this.scalaKernel %}
            command=command.replace(/(\w*?)\s*=\s*('(\\'|[^'])*'?)/g, function(a, b, c){
                return '("' + b + '","' + c.substring(1, c.length-1) + '")';
            })
            {% endif %}

            {# update the pd_control with the new command #}
            var rpattern=/,(.*?)='(.*?)'/g;
            var newOptions = {};
            for (var match = rpattern.exec(command); match != null; match = rpattern.exec(command)){
                newOptions[match[1]] = match[2];
            }
            pd_controls.options = newOptions;
            pd_controls.command = command;
        }
        if(curCell&&curCell.output_area){ 
            if ( !user_controls.nostoreMedatadata ){
                curCell._metadata.pixiedust = curCell._metadata.pixiedust || {}
                curCell._metadata.pixiedust.displayParams=displayParams
                curCell.output_area.outputs=[];
                var old_msg_id = curCell.last_msg_id;
                if (old_msg_id) {
                    curCell.kernel.clear_callbacks_for_msg(old_msg_id);
                }
            }
        }else{
            console.log("couldn't find the cell");
        }
        $('#wrapperJS' + pd_prefix).html("")
        if (!getTargetNode().hasClass( "no_loading_msg" )){
            setHTML(getTargetNode(), 
                '<div style="width:100px;height:60px;left:47%;position:relative">'+
                    '<i class="fa fa-circle-o-notch fa-spin" style="font-size:48px"></i>'+
                '</div>'+
                '<div style="text-align:center">' +
                    (getTargetNode().attr("pd_loading_msg") || "Loading your data. Please wait...") +
                '</div>',
                pd_controls, user_controls
            );
        }
        {% if gateway %}
        $.post({
            url: "/executeCode/" + pd_controls.options.gateway,
            data: command, 
            contentType: "text/plain",
            success: function(data){
                data = JSON.parse(data);
                data.forEach( function(msg){
                    if (msg.channel == "iopub"){
                        callbacks.iopub.output(msg);
                    }
                });
                console.log("result: ", data);
            }
        });
        {%else%}
        if (curCell && checkRootInit() && curCell._metadata.pixiedust && curCell._metadata.pixiedust.pixieapp){
            pd_controls.entity = pd_controls.entity || []
            if (pd_controls.entity.length == 1 && (pd_controls.options.nostore_pixieapp == pd_controls.entity[0])){
                console.log("Initializing pixieapp metadata");
                command = pd_controls.options.nostore_pixieapp + ".append_metadata(" + 
                JSON.stringify(curCell._metadata.pixiedust.pixieapp) + ")\n" + command
            }
        }
        if (user_controls.send_input_reply){
            command = user_controls.send_input_reply;
            callbacks.answer_input_reply = user_controls.answer_input_reply;
            {#remove any no_op command to avoid hang#}
            pixiedust.input_reply_queue.queue = pixiedust.input_reply_queue.queue.filter(
                function(item){
                    return item.command!='no_op';
                }
            );
            if (pixiedust.input_reply_queue.inflight || pixiedust.input_reply_queue.queue.length > 0 || command == "no_op_delay"){
                pixiedust.input_reply_queue.queue.push({"command":command, "callbacks":callbacks});
            }else{
                send_input_reply(callbacks, command, pd_controls);
            }
        }else{
            if (pixiedust.input_reply_queue.inflight){
                console.log("Warning: A kernel request is triggered but not all the reply callback where consummed", command);
            }
            command = command.trim();
            IPython.notebook.session.kernel.execute(command, callbacks, {
                silent:true,store_history:false,stop_on_error:true,allow_stdin : true
            });
        }
        {%endif%}

        console.log("Running command2:\n",command);
    }
}()
