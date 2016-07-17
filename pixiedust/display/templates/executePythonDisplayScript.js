function() {
    cellId = typeof cellId === "undefined" ? "" : cellId;
    var curCell=IPython.notebook.get_cells().filter(function(cell){
        return cell.cell_id=="{{this.options.get("cell_id","cellId")}}".replace("cellId",cellId);
    });
    curCell=curCell.length>0?curCell[0]:null;
    console.log("curCell",curCell);
    //Resend the display command
    var callbacks = {
        iopub:{
            output:function(msg){
                if ({{"false" if "cell_id" in this.options else "true"}}){
                    return curCell.output_area.handle_output.apply(curCell.output_area, arguments);
                }
                var msg_type=msg.header.msg_type;
                var content = msg.content;
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
                        $('#wrapperJS{{prefix}}').html("<script type=\\\"text/javascript\\\">"+content.data["application/javascript"]+"</s" + "cript>");
                    }
                    
                    if (html){
                        if(curCell&&curCell.output_area&&curCell.output_area.outputs){
                            var data = JSON.parse(JSON.stringify(content.data));
                            if(!!data["text/html"])data["text/html"]=html;
                            curCell.output_area.outputs.push({"data": data,"metadata":content.metadata,"output_type":msg_type});
                        }
                        $('#wrapperHTML{{prefix}}').html(html);
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
                console.log("msg", msg);
            }
        }
    }
    
    if (IPython && IPython.notebook && IPython.notebook.session && IPython.notebook.session.kernel){
        var command = "{{this._genDisplayScript(menuInfo)}}".replace("cellId",cellId);
        // get the selected column from the modal
        // this is a test and needs to be more generic (load options from DisplayHandler, etc)
        var colSelect = document.getElementById("column{{prefix}}");
        if (colSelect) {
            var startIndex, endIndex;
            startIndex = command.indexOf(",col='");
            if (startIndex >= 0) {
                endIndex = command.indexOf("'", startIndex+1);
                endIndex = command.indexOf("'", endIndex+1) + 1;
            }
            else {
                startIndex = endIndex = command.lastIndexOf(")");
            }
            var start = command.substring(0,startIndex);
            var end = command.substring(endIndex);
            command = start + ",col='" + colSelect.options[colSelect.selectedIndex].value + "'" + end;
        }
        console.log("Running command",command);
        if(curCell&&curCell.output_area)curCell.output_area.outputs=[];
        $('#wrapperJS{{prefix}}').html("")
        $('#wrapperHTML{{prefix}}').html('<div style="width:100px;height:60px;left:47%;position:relative"><i class="fa fa-circle-o-notch fa-spin" style="font-size:48px"></i></div>'+
        '<div style="text-align:center">Loading your data. Please wait...</div>');
        IPython.notebook.session.kernel.execute(command, callbacks, {silent:false,store_history:false,stop_on_error:true});
    }
}