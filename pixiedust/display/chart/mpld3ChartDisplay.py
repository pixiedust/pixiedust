# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2016
# 
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -------------------------------------------------------------------------------

from .baseChartDisplay import BaseChartDisplay
from .display import ChartDisplay
from .plugins.chart import ChartPlugin
from .plugins.dialog import DialogPlugin
from .plugins.elementInfo import ElementInfoPlugin
from abc import abstractmethod
from pyspark.sql import functions as F
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import mpld3
import mpld3.plugins as plugins

class Mpld3ChartDisplay(BaseChartDisplay):

    @abstractmethod
    def doRenderMpld3(self, handlerId, fig, ax, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues):
        pass

    def doRenderChart(self, handlerId, dialogTemplate, dialogOptions, aggregation, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues):
        # go
        fig, ax = plt.subplots(figsize=(6,4))
        dialogBody = self.renderTemplate(dialogTemplate, **dialogOptions)
        if (len(keyFieldLabels) > 0 and self.supportsKeyFieldLabels(handlerId) and self.supportsAggregation(handlerId)):
            plugins.connect(fig, ChartPlugin(self, keyFieldLabels))
        plugins.connect(fig, DialogPlugin(self, handlerId, dialogBody))
        colormap = cm.jet
        self.doRenderMpld3(handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues)
        self.setChartSize(handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues)
        self.setChartGrid(handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues)
        self.setChartLegend(handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues)
        self.setChartTitle(handlerId)

        #Render the figure
        self.renderFigure(fig, dialogBody)

    def renderFigure(self, fig, dialogBody):
        if self.options.get("staticFigure","false") is "true":
            import StringIO
            png=StringIO.StringIO()
            plt.savefig(png)
            self._addHTMLTemplate("mpld3Chart.html", 
                mpld3Figure="""<img src="data:image/png;base64,{0}">""".format(png.getvalue().encode('base64')), 
                optionsDialogBody=dialogBody)
            plt.close(fig)
        else:
            mpld3.enable_notebook()
            self._addHTMLTemplate("mpld3Chart.html", mpld3Figure=mpld3.fig_to_html(fig), optionsDialogBody=dialogBody)
            plt.close(fig)
            mpld3.disable_notebook()

    def connectElementInfo(self, element, data):
        if not hasattr(element, "get_figure") and hasattr(element,"get_children"):
            for i,child in enumerate(element.get_children()):
                plugins.connect(child.get_figure(), ElementInfoPlugin(child,data[i]))
        elif hasattr(element, "get_figure"):
            plugins.connect(element.get_figure(), ElementInfoPlugin(element, data ))
        