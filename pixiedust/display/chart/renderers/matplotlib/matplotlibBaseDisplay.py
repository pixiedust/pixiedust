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
from pixiedust.display.chart.renderers.baseChartDisplay import commonChartOptions
from pixiedust.utils import Logger
from ..baseChartDisplay import BaseChartDisplay
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from six import with_metaclass
from abc import abstractmethod, ABCMeta
import numpy as np

try:
    import mpld3
    import mpld3.plugins as plugins
    from pixiedust.display.chart.plugins.chart import ChartPlugin
    from pixiedust.display.chart.plugins.dialog import DialogPlugin
    from pixiedust.display.chart.plugins.elementInfo import ElementInfoPlugin
    mpld3Available = True
except ImportError:
    mpld3Available = False

@PixiedustRenderer(rendererId="matplotlib")
@Logger()
class MatplotlibBaseDisplay(with_metaclass(ABCMeta, BaseChartDisplay)):

    @abstractmethod
    def matplotlibRender(self):
        pass

    @property
    def useMpld3(self):
        return mpld3Available and self.options.get("mpld3", "false") == "true"

    @commonChartOptions
    def getChartOptions(self):
        if not mpld3Available:
            return []
        return [
            {
                'name': 'mpld3',
                'description': 'D3 Rendering (mpld3)',
                'metadata': {
                    'type': 'checkbox',
                    'default': "false"
                }
            }
        ]
        
    def setChartGrid(self, fig, ax):
        ax.grid(color='lightgray', alpha=0.7)

    def setTicks(self, fig, ax):
        labels = [s.get_text() for s in ax.get_xticklabels()]
        numChars = sum(len(s) for s in labels) * 5
        if numChars > self.getPreferredOutputWidth():
            #filter down the list to max 20        
            xl = [(i,a) for i,a in enumerate(labels) if i % int(len(labels)/20) == 0]
            ax.set_xticks([x[0] for x in xl])
            ax.set_xticklabels([x[1] for x in xl])

            #check if it still fits
            numChars = sum(len(s[1]) for s in xl) * 5
            if numChars > self.getPreferredOutputWidth():
                ax.tick_params(axis='x', labelsize=8 if numChars < 1200 else 6)
                plt.xticks(rotation=30)
            else:
                plt.xticks(rotation=0)
        else:
            plt.xticks(rotation=0)

    def setChartLegend(self, fig, ax):
        if self.supportsLegend(self.handlerId):
            showLegend = self.options.get("showLegend", "true")
            if showLegend == "true":
                l = ax.legend(title=self.titleLegend if hasattr(self, 'titleLegend') else '')
                if l is not None:
                    l.get_frame().set_alpha(0)
                    numColumns = len(self.getKeyFields())
                    for i, text in enumerate(l.get_texts()):
                        text.set_color(self.colormap(1.*i/numColumns))
                    for i, line in enumerate(l.get_lines()):
                        line.set_color(self.colormap(1.*i/numColumns))
                        line.set_linewidth(10)

    def getNumFigures(self):
        return 1    #default, subclasses can override

    def createFigure(self):
        numFigures = self.getNumFigures()
        if numFigures <= 1:
            return plt.subplots(figsize=( int(self.getPreferredOutputWidth()/ self.getDPI()), int(self.getPreferredOutputHeight() / self.getDPI()) ))

        gridCols = 2 #number of columns for a multiplots, TODO make the layout configurable
        numRows = int( numFigures/2 ) + numFigures % 2
        numCols = 2
        imageHeight =  ((self.getPreferredOutputWidth()/2) * 0.75) * numRows
        fig,ax = plt.subplots(numRows, numCols, figsize=( int(self.getPreferredOutputWidth()/self.getDPI()), int(imageHeight/self.getDPI() )))
        if numFigures%2 != 0:
            fig.delaxes(ax.item(numFigures))
            ax = np.delete(ax,numFigures)
        return (fig,ax)
        
    def doRenderChart(self):
        self.colormap = cm.jet

        fig = None
        try:
            # go
            fig, ax = self.createFigure()

            if self.useMpld3:
                #TODO: rework this piece
                #keyFieldLabels = self.getKeyFieldLabels()
                #if (len(keyFieldLabels) > 0 and self.supportsKeyFieldLabels(self.handlerId) and self.supportsAggregation(self.handlerId)):
                #    plugins.connect(fig, ChartPlugin(self, keyFieldLabels))
                plugins.connect(fig, DialogPlugin(self, self.handlerId, self.dialogBody))

            #let subclass do the actual rendering
            self.matplotlibRender(fig, ax)

            #finalize the chart
            if not isinstance(ax, (list,np.ndarray)):
                self.setChartGrid(fig, ax)
                self.setChartLegend(fig, ax)
                self.setTicks(fig, ax)

            #Render the figure
            return self.renderFigure(fig)
        finally:
            plt.close(fig)

    def renderFigure(self, fig):
        if not self.useMpld3:
            import base64
            try:
                from io import BytesIO as pngIO
            except ImportError:
                from StringIO import StringIO as pngIO
            png=pngIO()
            plt.savefig(png, pad_inches=0.05, bbox_inches='tight', dpi=self.getDPI())
            try:
                return """<center><img src="data:image/png;base64,{0}"  class="pd_save"></center>""".format(
                    base64.b64encode(png.getvalue()).decode("ascii")
                )
            finally:
                png.close()
        else:
            mpld3.enable_notebook()
            try:
                return mpld3.fig_to_html(fig)
            finally:
                mpld3.disable_notebook()

    def connectElementInfo(self, element, data):
        if not hasattr(element, "get_figure") and hasattr(element,"get_children"):
            for i,child in enumerate(element.get_children()):
                plugins.connect(child.get_figure(), ElementInfoPlugin(child,data[i]))
        elif hasattr(element, "get_figure"):
            plugins.connect(element.get_figure(), ElementInfoPlugin(element, data ))