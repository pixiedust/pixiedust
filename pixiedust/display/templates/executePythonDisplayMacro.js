{% macro executeDisplayfunction(options="{}", useCellMetadata=False, divId=None) -%}
{% set targetId=divId if divId and divId.startswith("$") else ("'"+divId+"'") if divId else "'wrapperHTML" + prefix + "'" %}
function() {
    function getTargetNode(){
        var n = $('#' + {{targetId}});
        if (n.length == 0 ){
            n = $('#wrapperHTML{{prefix}}');
        }
        return n;
    }
    cellId = typeof cellId === "undefined" ? "" : cellId;
    var curCell=IPython.notebook.get_cells().filter(function(cell){
        return cell.cell_id=="{{this.options.get("cell_id","cellId")}}".replace("cellId",cellId);
    });
    curCell=curCell.length>0?curCell[0]:null;
    console.log("curCell",curCell);
    var startWallToWall;
    //Resend the display command
    var callbacks = {
        shell : {
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
                console.log("msg", msg);
                if ({{"false" if "cell_id" in this.options else "true"}}){
                    //curCell.output_area.clear_output(false, true);
                    curCell.output_area.handle_output.apply(curCell.output_area, arguments);
                    return;
                }
                var msg_type=msg.header.msg_type;
                var content = msg.content;
                var executionTime = $("#execution{{prefix}}");
                if(msg_type==="stream"){
                    getTargetNode().html(content.text);
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
                        if (pixiedust){
                            if (callbacks.options && callbacks.options.nostore_delaysave){
                                setTimeout(function(){
                                    pixiedust.saveOutputInCell(curCell, content, html, msg_type);
                                }, 1000);
                            }else{
                                pixiedust.saveOutputInCell(curCell, content, html, msg_type);
                            }                         
                        }

                        try{
                            getTargetNode().html(html);
                        }catch(e){
                            console.log("Invalid html output", e, html);
                            getTargetNode().html( "Invalid html output: " + e.message + "<pre>" 
                                + html.replace(/>/g,'&gt;').replace(/</g,'&lt;').replace(/"/g,'&quot;') + "<pre>");
                        }
                    }
                }else if (msg_type === "error") {
                    require(['base/js/utils'], function(utils) {
                        var tb = content.traceback;
                        console.log("tb",tb);
                        if (tb && tb.length>0){
                            var data = tb.reduce(function(res, frame){return res+frame+'\\n';},"");
                            console.log("data",data);
                            data = utils.fixConsole(data);
                            data = utils.fixCarriageReturn(data);
                            data = utils.autoLinkUrls(data);
                            getTargetNode().html("<pre>" + data +"</pre>");
                        }
                    });
                }

                //Append profiling info
                if (executionTime.length > 0 && $("#execution{{prefix}}").length == 0 ){
                    getTargetNode().append(executionTime);
                }else if (startWallToWall && $("#execution{{prefix}}").length > 0 ){
                    $("#execution{{prefix}}").append($("<div/>").text("Wall to Wall time: " + ( (new Date().getTime() - startWallToWall)/1000 ) + "s"));
                }

                if (typeof onDisplayDone{{prefix}} != "undefined"){
                    onDisplayDone{{prefix}}();
                }
                $(document).trigger('pd_event', {type:"pd_load", targetNode: getTargetNode()});
            }
        }
    }
    
    if (IPython && IPython.notebook && IPython.notebook.session && IPython.notebook.session.kernel){
        var command = "{{this._genDisplayScript(menuInfo)}}".replace("cellId",cellId);
        function addOptions(options, override=true){
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
        }
        if(typeof cellMetadata != "undefined" && cellMetadata.displayParams){
            addOptions(cellMetadata.displayParams);
        }else if (curCell && curCell._metadata.pixiedust ){
            addOptions(curCell._metadata.pixiedust.displayParams || {}, ('{{useCellMetadata}}'=='True') );
        }
        addOptions({{options|oneline|trim}});
        {#Give a chance to the caller to add extra template fragment here#}
        {{caller()}}
        {%if not this.nostore_params%}
        var pattern = "\\w*\\s*=\\s*'(\\\\'|[^'])*'";
        var rpattern=new RegExp(pattern,"g");
        var n = command.match(rpattern);
        {#find the org_params if any#}
        var org_params = {}
        callbacks.options = callbacks.options || {};
        for (var i=0; i<n.length;i++){
            var parts = n[i].split("=")
            callbacks.options[parts[0].trim()] = parts[1].trim();
            if (parts[0].trim() == "org_params"){
                var value = parts[1].trim()
                var values = value.substring(1,value.length-1).split(",");
                for (var p in values){
                    org_params[values[p].trim()] = true;
                }
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
        if(curCell&&curCell.output_area){
            curCell._metadata.pixiedust = curCell._metadata.pixiedust || {}
            curCell._metadata.pixiedust.displayParams=displayParams
            curCell.output_area.outputs=[];
            var old_msg_id = curCell.last_msg_id;
            if (old_msg_id) {
                curCell.kernel.clear_callbacks_for_msg(old_msg_id);
            }
        }else{
            console.log("couldn't find the cell");
        }
        {%endif%}
        $('#wrapperJS{{prefix}}').html("")
        getTargetNode().html('<div style="width:100px;height:60px;left:47%;position:relative"><i class="fa fa-circle-o-notch fa-spin" style="font-size:48px"></i></div>'+
        '<div style="text-align:center">Loading your data. Please wait...</div>');
        startWallToWall = new Date().getTime();
        {% if this.scalaKernel %}
        command=command.replace(/(\w*?)\s*=\s*('(\\'|[^'])*'?)/g, function(a, b, c){
            return '("' + b + '","' + c.substring(1, c.length-1) + '")';
        })
        {% endif %}
        console.log("Running command2",command);
        IPython.notebook.session.kernel.execute(command, callbacks, {silent:true,store_history:false,stop_on_error:true});
    }
}
{% endmacro %}

{% macro executeDisplay(options="{}",useCellMetadata=False, divId=None) -%}
    {%if caller%}
        {% set content=caller() %}
    {%else%}
        {% set content="" %}
    {%endif%}
    !{%call executeDisplayfunction(options, useCellMetadata, divId)%}
        {{content}}
    {%endcall%}()
{%- endmacro %}