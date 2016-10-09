{% macro executeDisplayfunction(options="{}", useCellMetadata=False) -%}
function() {
    cellId = typeof cellId === "undefined" ? "" : cellId;
    var curCell=IPython.notebook.get_cells().filter(function(cell){
        return cell.cell_id=="{{this.options.get("cell_id","cellId")}}".replace("cellId",cellId);
    });
    curCell=curCell.length>0?curCell[0]:null;
    console.log("curCell",curCell);
    var startWallToWall;
    //Resend the display command
    var callbacks = {
        iopub:{
            output:function(msg){
                console.log("msg", msg);
                if ({{"false" if "cell_id" in this.options else "true"}}){
                    return curCell.output_area.handle_output.apply(curCell.output_area, arguments);
                }
                var msg_type=msg.header.msg_type;
                var content = msg.content;
                var executionTime = $("#execution{{prefix}}");
                if(msg_type==="stream"){
                    $('#wrapperHTML{{prefix}}').html(content.text);
                }else if (msg_type==="display_data" || msg_type==="execute_result"){
                    var html=null;
                    if (!!content.data["text/html"]){
                        html=content.data["text/html"];
                    }else if (!!content.data["image/png"]){
                        html=html||"";
                        html+="<img src='data:image/png;base64," +content.data["image/png"]+"'></img>";
                    }
                                                    
                    if (!!content.data["application/javascript"]){
                        try{
                            $('#wrapperJS{{prefix}}').html("<script type=\\\"text/javascript\\\">"+content.data["application/javascript"]+"</s" + "cript>");
                        }catch(e){
                            console.log("Invalid javascript output",e, content.data);
                        }
                    }
                    
                    if (html){
                        if(curCell&&curCell.output_area&&curCell.output_area.outputs){
                            var data = JSON.parse(JSON.stringify(content.data));
                            if(!!data["text/html"])data["text/html"]=html;
                            curCell.output_area.outputs.push({"data": data,"metadata":content.metadata,"output_type":msg_type});
                        }
                        try{
                            $('#wrapperHTML{{prefix}}').html(html);
                        }catch(e){
                            console.log("Invalid html output", e, html);
                            $('#wrapperHTML{{prefix}}').html( "Invalid html output. <pre>" 
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
                            $('#wrapperHTML{{prefix}}').html("<pre>" + data +"</pre>");
                        }
                    });
                }

                //Append profiling info
                if (executionTime.length > 0 && $("#execution{{prefix}}").length == 0 ){
                    $('#wrapperHTML{{prefix}}').append(executionTime);
                }else if (startWallToWall && $("#execution{{prefix}}").length > 0 ){
                    $("#execution{{prefix}}").append($("<div/>").text("Wall to Wall time: " + ( (new Date().getTime() - startWallToWall)/1000 ) + "s"));
                }
            }
        }
    }
    
    if (IPython && IPython.notebook && IPython.notebook.session && IPython.notebook.session.kernel){
        var command = "{{this._genDisplayScript(menuInfo)}}".replace("cellId",cellId);
        function addOptions(options){
            function getStringRep(v) {
                if (!isNaN(parseFloat(v)) && isFinite(v)){
                    return v.toString();
                }
                return "'" + v + "'";
            }
            for (var key in options){
                var value = options[key];
                var hasValue = value != null && typeof value !== 'undefined' && value !== '';
                var replaceValue = hasValue ? (key+"=" + getStringRep(value) ) : "";
                var pattern = (hasValue?"":",")+"\\s*" + key + "\\s*=\\s*'(\\\\'|[^'])*'";
                var rpattern=new RegExp(pattern);
                var n = command.search(rpattern);
                if ( n >= 0 ){
                    command = command.replace(rpattern, replaceValue);
                }else if (hasValue){
                    var n = command.lastIndexOf(")");
                    command = [command.slice(0, n), (command[n-1]=="("? "":",") + replaceValue, command.slice(n)].join('')
                }        
            }
        }
        if(typeof cellMetadata != "undefined" && cellMetadata.displayParams){
            addOptions(cellMetadata.displayParams);
            addOptions({"showchrome":"true"});
        }else if ('{{useCellMetadata}}'=='True' && curCell && curCell._metadata.pixiedust ){
            addOptions(curCell._metadata.pixiedust.displayParams || {} );
        }
        addOptions({{options|oneline|trim}});
        {#Give a chance to the caller to add extra template fragment here#}
        {{caller()}}
        console.log("Running command2",command);
        var pattern = "\\w*\\s*=\\s*'(\\\\'|[^'])*'";
        var rpattern=new RegExp(pattern,"g");
        var n = command.match(rpattern);
        var displayParams={}
        for (var i = 0; i < n.length; i++){
            var parts=n[i].split("=");
            var key = parts[0].trim();
            var value = parts[1].trim()
            if (!key.startsWith("nostore_") && key != "showchrome" && key != "prefix" && key != "cell_id"){
                displayParams[key] = value.substring(1,value.length-1);
            }
        }
        if(curCell&&curCell.output_area){
            curCell._metadata.pixiedust = curCell._metadata.pixiedust || {}
            curCell._metadata.pixiedust.displayParams=displayParams
            curCell.output_area.outputs=[];
        }
        $('#wrapperJS{{prefix}}').html("")
        $('#wrapperHTML{{prefix}}').html('<div style="width:100px;height:60px;left:47%;position:relative"><i class="fa fa-circle-o-notch fa-spin" style="font-size:48px"></i></div>'+
        '<div style="text-align:center">Loading your data. Please wait...</div>');
        startWallToWall = new Date().getTime();
        IPython.notebook.session.kernel.execute(command, callbacks, {silent:false,store_history:false,stop_on_error:true});
    }
}
{% endmacro %}

{% macro executeDisplay(options="{}",useCellMetadata=False) -%}
    !{%call executeDisplayfunction(options, useCellMetadata)%}{%endcall%}()
{%- endmacro %}