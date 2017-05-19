# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2017
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
import math
import matplotlib.ticker as ticker

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

    def __init__(self, options, entity, dataHandler=None):
        super(MatplotlibBaseDisplay,self).__init__(options,entity,dataHandler)
        self.needsStretching = False

    @abstractmethod
    def matplotlibRender(self):
        pass

    @property
    def useMpld3(self):
        return mpld3Available and self.options.get("mpld3", "false") == "true"

    def canStretch(self):
        return True

    def isStretchingOn(self):
        return self.getBooleanOption('stretch', False) and not self.useMpld3

    @commonChartOptions
    def getChartOptions(self):
        options = []
        if mpld3Available:
            options.append({
                'name': 'mpld3',
                'refresh': True,
                'description': 'D3 Rendering (mpld3)',
                'metadata': {
                    'type': 'checkbox',
                    'default': "false"
                }
            })
        if self.needsStretching:
            options.append({
                'name': 'stretch',
                'description': 'Stretch image',
                'metadata':{
                    'type': 'checkbox',
                    'default': 'false'
                }
            })
        return options

    def setTicks(self, fig, ax):
        if self.handlerId=="lineChart" and self.getBooleanOption("logy",False):
            start, end = ax.get_ylim()
            ax.yaxis.set_minor_locator(ticker.MultipleLocator((end - start) / 4))
            ax.yaxis.set_minor_formatter(ticker.LogFormatter(labelOnlyBase=False))
            ax.grid(True, which='both')

        labels = [s.get_text() for s in ax.get_xticklabels()]
        totalWidth = sum(len(s) for s in labels) * 5
        if totalWidth > self.getPreferredOutputWidth():
            self.needsStretching = self.canStretch()
            if self.isStretchingOn():
                #resize image width
                fig.set_size_inches(min(totalWidth/self.getDPI(), 32768/self.getDPI()),fig.get_figheight())
            else:
                self.addMessage("Some labels are not displayed because of a lack of space. Click on Stretch image to see them all")
                #filter down the list to max 20
                max = int(len(labels)/20)
                if max < 20:
                    xl = [(i,a[:10] + ".." if len(a) > 10 else a) for i,a in enumerate(labels)]
                else:
                    xl = [(i,a) for i,a in enumerate(labels) if (i % max == 0)]
                ax.set_xticks([x[0] for x in xl])
                ax.set_xticklabels([x[1] for x in xl])
                plt.xticks(rotation=30)
        else:
            plt.xticks(rotation=0)

    def setLegend(self, fig, ax):
        if ax.get_legend() is not None:
            numLabels = len(ax.get_legend_handles_labels()[1])
            nCol = int(min(max(math.sqrt( numLabels ), 3), 6))
            nRows = int(numLabels/nCol)
            bboxPos = max(1.15, 1.0 + ((float(nRows)/2)/10.0))
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, bboxPos),ncol=nCol, fancybox=True, shadow=True)

    def getNumFigures(self):
        return 1    #default, subclasses can override

    def createFigure(self):
        numFigures = self.getNumFigures()
        if numFigures <= 1:
            return plt.subplots(figsize=( int(self.getPreferredOutputWidth()/ self.getDPI()), int(self.getPreferredOutputHeight() / self.getDPI()) ))

        numCols = 1 if self.isStretchingOn() else 2 #number of columns for a multiplots, TODO make the layout configurable
        numRows = int( numFigures/numCols ) + numFigures % numCols
        imageHeight =  ((self.getPreferredOutputWidth()/numCols) * self.getHeightWidthRatio()) * numRows
        fig,ax = plt.subplots(numRows, numCols, figsize=( int(self.getPreferredOutputWidth()/self.getDPI()), int(imageHeight/self.getDPI() )))
        if numFigures%numCols != 0:
            fig.delaxes(ax.item(numFigures))
            ax = np.delete(ax,numFigures)
        return (fig,ax)

    def getSubplotHSpace(self):
        return 0.5 if self.isStretchingOn() else 0.3
        
    def doRenderChart(self):
        self.colormap = cm.jet

        # set defaults for plot
        plt.rcParams['savefig.dpi'] = 96
        plt.rcParams['font.family'] = "serif"
        plt.rcParams['font.serif'] = "cm"
        
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
            newAx = self.matplotlibRender(fig, ax)
            if newAx is not None:
                ax = newAx

            axes = ax
            if not isinstance(axes, (list,np.ndarray)):
                axes = np.asarray([axes])

            #finalize the chart
            for i, a in np.ndenumerate(axes):
                if a.title is None or not a.title.get_visible() or a.title.get_text() == '':
                    self.setLegend(fig, a)
                self.setTicks(fig, a)
            sharex = True if len(axes) <=1 else len([a for a in axes if a._sharex is not None]) > 0
            if len(axes)>1 and not sharex:
                #adjust the height between subplots
                plt.subplots_adjust(hspace=self.getSubplotHSpace())

            #mpld3 has a bug when autolocator are used. Change to FixedLocators
            if self.useMpld3:
                self.addMessage("Warning: While great, D3 rendering is using MPLD3 library which has limitations that have not yet been fixed")
                from matplotlib import ticker
                self.debug("Converting to FixedLocator for mpld3")
                for a in axes:
                    locator = a.xaxis.get_major_locator()
                    if not isinstance(locator, ticker.FixedLocator):
                        vmin,vmax = a.xaxis.get_data_interval()
                        a.xaxis.set_major_locator(ticker.FixedLocator(locator.tick_values(vmin, vmax)))

            #Render the figure
            return self.renderFigure(fig)
        finally:
            if fig is not None:
                plt.close(fig)

    def renderFigure(self, fig):
        def genMarkup(chartFigure):
            return self.env.from_string("""
                    {0}
                    {{%for message in messages%}}
                        <div>{{{{message}}}}</div>
                    {{%endfor%}}
                """.format(chartFigure)
            ).render(messages=self.messages)
            
        if not self.useMpld3:
            import base64
            try:
                from io import BytesIO as pngIO
            except ImportError:
                from StringIO import StringIO as pngIO
            png=pngIO()
            plt.savefig(png, pad_inches=0.05, bbox_inches='tight', dpi=self.getDPI())
            try:
                return( 
                    genMarkup("""
                            <center><img style="max-width:initial !important" src="data:image/png;base64,{0}"  class="pd_save"></center>
                        """.format(base64.b64encode(png.getvalue()).decode("ascii"))
                    )
                )
            finally:
                png.close()
        else:
            mpld3.enable_notebook()
            try:
                return genMarkup(mpld3.fig_to_html(fig))
            finally:
                mpld3.disable_notebook()

    def connectElementInfo(self, element, data):
        if not hasattr(element, "get_figure") and hasattr(element,"get_children"):
            for i,child in enumerate(element.get_children()):
                plugins.connect(child.get_figure(), ElementInfoPlugin(child,data[i]))
        elif hasattr(element, "get_figure"):
            plugins.connect(element.get_figure(), ElementInfoPlugin(element, data ))

    """
    Helper to safely access i position of an ax object
    """
    def getAxItem(self, ax, pos):
        if isinstance(ax, np.ndarray):
            return ax.item(pos)
        elif pos == 0:
            return ax
        raise ValueError("Trying to access pos {} from a single ax".format(pos))
