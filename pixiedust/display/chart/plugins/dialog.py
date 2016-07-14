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