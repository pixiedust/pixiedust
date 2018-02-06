!function() {
    function getTargetNode(){
        return $('#' + ($targetDivId || ("wrapperHTML"+ pd_prefix)));
    }
    function checkRootInit(){
        node = getTargetNode();
        var retValue = node.is("[pd_init]");
        if (retValue){
            node.removeAttr("pd_init");
        }
        return retValue;
    }
    function setHTML(targetNode, contents, pdCtl = null){
        var pd_elements = []
        targetNode.children().each(function(){
            if (this.tagName.toLowerCase().startsWith("pd_")){
                pd_elements.push($(this).clone());
            }
        });
        targetNode.html("<div pd_stop_propagation style='height:100%;'>" + contents + "</div>");
        if (pd_elements.length > 0 ){
            targetNode.append(pd_elements);
        }
        return true;
    }
    var cellId = options.cell_id || "";
    var curCell = pixiedust.getCell(cellId);
    console.log("curCell",curCell);
    var startWallToWall;
    //Resend the display command
    var callbacks = {
        shell : {
            reply : function(){
                if ( !callbacks.response ){
                    if (!user_controls.partialUpdate){
                        setHTML(getTargetNode(), "",pd_controls);
                        if (user_controls.onDisplayDone){
                            user_controls.onDisplayDone(getTargetNode());
                        }
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
                    if (user_controls.onSuccess){
                        user_controls.onSuccess(content.text);
                    }else{
                        targetNodeUpdated = setHTML(getTargetNode(), content.text, pd_controls);
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
                                targetNodeUpdated = setHTML(getTargetNode(), html, pd_controls);
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
                                pd_controls);
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
                    targetNodeUpdated = setHTML(getTargetNode(), content.traceback, pd_controls);
                    {%else%}
                    require(['base/js/utils'], function(utils) {
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
                                targetNodeUpdated = setHTML(getTargetNode(), "<pre>" + data +"</pre>", pd_controls);
                            }
                        }
                    });
                    {%endif%}
                }else{
                    callbacks.response = false;
                }
                if (targetNodeUpdated && user_controls.onDisplayDone){
                    user_controls.onDisplayDone(getTargetNode());
                }
            }
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
                pd_controls
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
        IPython.notebook.session.kernel.execute(command, callbacks, {silent:true,store_history:false,stop_on_error:true});
        {%endif%}

        console.log("Running command2:\n",command);
    }
}()
