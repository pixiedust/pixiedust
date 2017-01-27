{% macro executeDisplayfunction(options="{}", useCellMetadata=False, divId=None) -%}
{% set targetId=divId if divId else "wrapperHTML" + prefix %}
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
                    curCell.output_area.handle_output.apply(curCell.output_area, arguments);
                    curCell.output_area.outputs=[];
                    return;
                }
                var msg_type=msg.header.msg_type;
                var content = msg.content;
                var executionTime = $("#execution{{prefix}}");
                if(msg_type==="stream"){
                    $('#{{targetId}}').html(content.text);
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
                            $('#{{targetId}}').html(html);
                        }catch(e){
                            console.log("Invalid html output", e, html);
                            $('#{{targetId}}').html( "Invalid html output. <pre>" 
                                + html.replace(/>/g,'&gt;').replace(/</g,'&lt;').replace(/"/g,'&quot;') + "<pre>");
                        }

                        if(curCell&&curCell.output_area&&curCell.output_area.outputs){
                            setTimeout(function(){
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
                            },2000);
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
                            $('#{{targetId}}').html("<pre>" + data +"</pre>");
                        }
                    });
                }

                //Append profiling info
                if (executionTime.length > 0 && $("#execution{{prefix}}").length == 0 ){
                    $('#{{targetId}}').append(executionTime);
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
            var old_msg_id = curCell.last_msg_id;
            if (old_msg_id) {
                curCell.kernel.clear_callbacks_for_msg(old_msg_id);
            }
        }else{
            console.log("couldn't find the cell");
        }
        $('#wrapperJS{{prefix}}').html("")
        $('#{{targetId}}').html('<div style="width:100px;height:60px;left:47%;position:relative"><i class="fa fa-circle-o-notch fa-spin" style="font-size:48px"></i></div>'+
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