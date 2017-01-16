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

from pixiedust.display.chart.renderers import PixiedustRenderer
from ..baseChartDisplay import BaseChartDisplay
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from six import with_metaclass
from abc import abstractmethod, ABCMeta

try:
    import mpld3
    import mpld3.plugins as plugins
    from pixiedust.display.chart.plugins.chart import ChartPlugin
    from pixiedust.display.chart.plugins.dialog import DialogPlugin
    from pixiedust.display.chart.plugins.elementInfo import ElementInfoPlugin
    mpld3Available = True
except ImportError:
    mpld3Available = False

import pixiedust
myLogger = pixiedust.getLogger(__name__)

@PixiedustRenderer(rendererId="matplotlib")
class MatplotlibBaseDisplay(with_metaclass(ABCMeta, BaseChartDisplay)):

    @abstractmethod
    def matplotlibRender(self):
        pass

    @property
    def has_mpld3(self):
        return mpld3Available

    """
        Subclass can override: return an array of option metadata
    """
    def getChartOptions(self):
        return []

    def setChartSize(self, fig, ax):
        params = plt.gcf()
        plSize = params.get_size_inches()
        params.set_size_inches((plSize[0]*1.5, plSize[1]*1.5))
        
    def setChartGrid(self, fig, ax):
        ax.grid(color='lightgray', alpha=0.7)

    def setChartTitle(self):
        title = self.options.get("title")
        if title is not None:
            plt.title(title, fontsize=30)

    def setChartLegend(self, fig, ax):
        if self.supportsLegend(self.handlerId):
            showLegend = self.options.get("showLegend", "true")
            if showLegend == "true":
                l = ax.legend(title=self.titleLegend if hasattr(self, 'titleLegend') else '')
                if l is not None:
                    keyFieldValues = self.getKeyFieldValues()
                    l.get_frame().set_alpha(0)
                    numColumns = len(keyFieldValues)
                    for i, text in enumerate(l.get_texts()):
                        text.set_color(self.colormap(1.*i/numColumns))
                    for i, line in enumerate(l.get_lines()):
                        line.set_color(self.colormap(1.*i/numColumns))
                        line.set_linewidth(10)

    def createFigure(self):
        return plt.subplots(figsize=(6,4))
        
    def doRenderChart(self):
        self.colormap = cm.jet

        # go
        fig, ax = self.createFigure()

        keyFieldLabels = self.getKeyFieldLabels()

        if self.has_mpld3:
            if (len(keyFieldLabels) > 0 and self.supportsKeyFieldLabels(self.handlerId) and self.supportsAggregation(self.handlerId)):
                plugins.connect(fig, ChartPlugin(self, keyFieldLabels))
            plugins.connect(fig, DialogPlugin(self, self.handlerId, self.dialogBody))

        #let subclass do the actual rendering
        self.matplotlibRender(fig, ax)

        self.setChartSize(fig, ax)
        self.setChartGrid(fig, ax)
        self.setChartLegend(fig, ax)
        self.setChartTitle()

        fig.autofmt_xdate()

        #Render the figure
        return self.renderFigure(fig)

    def renderFigure(self, fig):
        if not self.has_mpld3 or self.options.get("staticFigure","false") is "true":
            import base64
            try:
                from io import BytesIO as pngIO
            except ImportError:
                from StringIO import StringIO as pngIO
            png=pngIO()
            plt.savefig(png)
            try:
                return """<img width='100%' src="data:image/png;base64,{0}"  class="pd_save">""".format(
                    base64.b64encode(png.getvalue()).decode("ascii")
                )
            finally:
                png.close()
                plt.close(fig)
        else:
            mpld3.enable_notebook()
            try:
                return mpld3.fig_to_html(fig)
            finally:
                plt.close(fig)
                mpld3.disable_notebook()

    def connectElementInfo(self, element, data):
        if not hasattr(element, "get_figure") and hasattr(element,"get_children"):
            for i,child in enumerate(element.get_children()):
                plugins.connect(child.get_figure(), ElementInfoPlugin(child,data[i]))
        elif hasattr(element, "get_figure"):
            plugins.connect(element.get_figure(), ElementInfoPlugin(element, data ))