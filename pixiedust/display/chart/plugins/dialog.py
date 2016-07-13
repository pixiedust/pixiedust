from mpld3 import plugins

class DialogPlugin(plugins.PluginBase):  # inherit from PluginBase
    """Dialog plugin"""
    
    DEFAULT_JAVASCRIPT = """
    mpld3.register_plugin("dialog", DialogPlugin);
    DialogPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    DialogPlugin.prototype.constructor = DialogPlugin;
    DialogPlugin.prototype.requiredProps = ["handlerId"];    
    function DialogPlugin(fig, props) {{
        mpld3.Plugin.call(this, fig, props);
    	var DialogPluginButton = mpld3.ButtonFactory({{
        	buttonID: "DialogPlugin",
        	sticky: false,
        	onActivate: function() {{
                require(['base/js/dialog'],function(dialog) {{
                    var modal = dialog.modal;
                    var modal_obj = modal({{
                        title: "Chart Options",
                        body: "{0}",
                        sanitize: false,
                        buttons: {{
                            OK: {{ 
                                class : "btn-primary",
                                click: function() {{
                                    console.log("CLICKED: " + 'column{2}');
                                    ({1})()
                                }}
                            }},
                            Cancel: {{
                            }}
                        }}
                    }});
                    modal_obj.on('shown.bs.modal', function() {{
                    }});
                }});
            }},
        	icon: function() {{
            	return mpld3.icons["brush"];
        	}}
    	}});
    	this.fig.buttons.push(DialogPluginButton);
    }};
    """

    def __init__(self, handlerId, prefix, clickFunction, colNames, options):
        form = "<form id='options{0}'><select id='column{0}'>".format(prefix)
        form += "<option>ALL</option>"
        selected = ""
        for i, colName in enumerate(colNames):
            if (options.get("col") is colName):
                selected = " selected"
            else:
                selected = ""
            form += "<option value='{0}'{1}>{0}</option>".format(colName,selected)
        form += "</select></form>"
        DialogPlugin.JAVASCRIPT = DialogPlugin.DEFAULT_JAVASCRIPT.format(form, clickFunction, prefix)
        self.dict_ = {"type": "dialog", "handlerId": handlerId}

    # def _addOptionsButtonHtml(self, handlerId):
    #     self.html += self._getOptionsButtonHtml(handlerId)

    # def _getOptionsButtonHtml(self, handlerId):
    #     if handlerId is None:
    #         return "<script>console.log('handlerId is NULL');</script>"
    #     else:
    #         menuInfo = globalMenuInfos[handlerId]
    #         return """<div style='clear: both;'>
    #                 <button id='btn{0}'>Options</button>
    #                 <script>
    #                     console.log('handlerId is {2}')
    #                     $('#btn{0}').on('click', {1})
    #                 </script>
    #             </div>""".format(str(uuid.uuid4())[:8],self._getShowOptionsDialogPluginScript(menuInfo),handlerId)

    # def _getShowOptionsDialogPluginScript(self):
    #     return """function() {{
    #             require(['base/js/DialogPlugin'],function(DialogPlugin) {{
    #                 var modal = DialogPlugin.modal;
    #                 var modal_obj = modal({{
    #                     title: "Hello DialogPlugin",
    #                     body: "<div>this is the body of my DialogPlugin</div>",
    #                     buttons: {{
    #                         OK: {{ 
    #                             class : "btn-primary",
    #                             click: {0}
    #                         }},
    #                         Cancel: {{
    #                         }}
    #                     }}
    #                 }});
    #                 modal_obj.on('shown.bs.modal', function() {{
    #                 }});
    #             }});
    #         }}""".format(self._getSetOptionsScript())

    # def _getSetOptionsScript(self):
    #     return """function() {{
    #         cellId = typeof cellId === "undefined" ? "" : cellId;
    #         var curCell=IPython.notebook.get_cells().filter(function(cell){{return cell.cell_id=="{2}".replace("cellId",cellId);}});
    #         curCell=curCell.length>0?curCell[0]:null;
    #         console.log("curCell",curCell);
    #         if (IPython && IPython.notebook && IPython.notebook.session && IPython.notebook.session.kernel){{
    #                 var command = "{1}".replace("cellId",cellId);
    #                 console.log("Running command",command);
    #                 if(curCell&&curCell.output_area)curCell.output_area.outputs=[];
    #                 $('#wrapperJS{0}').html("")
    #                 $('#wrapperHTML{0}').html('<div style="width:100px;height:60px;left:47%;position:relative"><i class="fa fa-circle-o-notch fa-spin" style="font-size:48px"></i></div>'+
    #                 '<div style="text-align:center">Loading your data. Please wait...</div>');
    #                 IPython.notebook.session.kernel.execute(command, callbacks, {{silent:false,store_history:false,stop_on_error:true}});
    #             }}
    #         }}""".format(self.getPrefix(), self._genDisplayScript(menuInfo), self.options.get("cell_id","cellId"))