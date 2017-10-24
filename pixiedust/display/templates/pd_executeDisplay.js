!function() {
    function getTargetNode(){
        return $('#' + ($targetDivId || ("wrapperHTML"+ pd_prefix)));
    }
    function setHTML(targetNode, contents){
        var pd_elements = []
        targetNode.children().each(function(){
            if (this.tagName.toLowerCase().startsWith("pd_")){
                pd_elements.push($(this).clone());
            }
        })
        targetNode.html(contents);
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
                        setHTML(getTargetNode(), "");
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
                callbacks.response = true;
                console.log("msg", msg);
                if (cellId == ""){
                    if (curCell){
                        curCell.output_area.handle_output.apply(curCell.output_area, arguments);
                        curCell.output_area.outputs=[];
                    }else{
                        console.log("Could not find current cell");
                    }
                    return;
                }
                var msg_type=msg.header.msg_type;
                var content = msg.content;
                var targetNodeUpdated = false;
                if(msg_type==="stream"){
                    if (user_controls.onSuccess){
                        user_controls.onSuccess(content.text);
                    }else{
                        targetNodeUpdated = setHTML(getTargetNode(), content.text);
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
                                targetNodeUpdated = setHTML(getTargetNode(), html);
                            }
                        }catch(e){
                            console.log("Invalid html output", e, html);
                            targetNodeUpdated = setHTML(getTargetNode(),  "Invalid html output: " + e.message + "<pre>" 
                                + html.replace(/>/g,'&gt;').replace(/</g,'&lt;').replace(/"/g,'&quot;') + "<pre>");
                        }

                        if(curCell&&curCell.output_area&&curCell.output_area.outputs){
                            var data = JSON.parse(JSON.stringify(content.data));
                            if(!!data["text/html"])data["text/html"]=html;
                            function savedData(data){
                                {#hide the output when displayed with nbviewer on github, use the is-viewer-good class which is only available on github#}
                                var markup='<style type="text/css">.pd_warning{display:none;}</style>';
                                markup+='<div class="pd_warning"><em>Hey, there\'s something awesome here! To see it, open this notebook outside GitHub, in a viewer like Jupyter</em></div>';
                                nodes = $.parseHTML(data["text/html"], null, true);
                                var s = $(nodes).wrap("<div>").parent().find(".pd_save").not(".pd_save .pd_save")
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
                            curCell.output_area.outputs.push({"data": savedData(data),"metadata":content.metadata,"output_type":msg_type});
                        }
                    }
                }else if (msg_type === "error") {
                    {% if gateway %}
                    targetNodeUpdated = setHTML(getTargetNode(), content.traceback);
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
                                targetNodeUpdated = setHTML(getTargetNode(), "<pre>" + data +"</pre>");
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
                ignoreKeys = pd_controls.options.nostore_pixieapp?["handlerId"]:[];
                addOptions(curCell._metadata.pixiedust.displayParams || {}, pd_controls.useCellMetadata, ignoreKeys);
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
                '</div>'
            );
        }
        console.log("Running command2",command);
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
        IPython.notebook.session.kernel.execute(command, callbacks, {silent:true,store_history:false,stop_on_error:true});
        {%endif%}
    }
}()
