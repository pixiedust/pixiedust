from mpld3 import plugins

class ChartPlugin(plugins.PluginBase):  # inherit from PluginBase
    """Chart plugin to fix xticks that are overriden by mpld3 while converting from matplotlib """

    def __init__(self, display, xtick_labels):
        ChartPlugin.JAVASCRIPT = display.renderTemplate("chartPlugin.js")
        self.dict_ = {"type": "chart","labels": xtick_labels}