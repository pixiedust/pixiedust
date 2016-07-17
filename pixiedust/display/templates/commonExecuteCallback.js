{% macro ipython_execute(command, prefix) -%}

var callbacks = {
    iopub:{
        output:function(msg){
            var msg_type=msg.header.msg_type;
            var content = msg.content;
            if(msg_type==="stream"){
                {{caller("content.text")}}
            }else if (msg_type==="display_data" || msg_type==="execute_result"){
                if (!!content.data["text/html"]){
                    {{caller('content.data["text/html"]')}}
                }
            }else if (msg_type === "error") {
                require(['base/js/utils'], function(utils) {
                    var tb = content.traceback;
                    if (tb && tb.length>0){
                        var data = tb.reduce(function(res, frame){return res+frame+'\\n';},"");
                        data = utils.fixConsole(data);
                        data = utils.fixCarriageReturn(data);
                        data = utils.autoLinkUrls(data);
                        $('#loading{{prefix}}').html("<pre>" + data +"</pre>");
                    }
                });
            }
        }
    }
}

$('#loading{{prefix}}').css('display','block');
IPython.notebook.session.kernel.execute(
    "{{command}}", 
    callbacks, 
    {silent:false,store_history:false,stop_on_error:true}
);

{%- endmacro %}