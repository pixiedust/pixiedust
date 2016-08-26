from mpld3 import plugins

class DialogPlugin(plugins.PluginBase):  # inherit from PluginBase
    """Dialog plugin"""
    
    def __init__(self, display, handlerId, body):
        DialogPlugin.JAVASCRIPT = display.renderTemplate("chartOptionsDialogPlugin.js",optionsDialogBody=body)
        self.dict_ = {"type": "dialog", "handlerId": handlerId}