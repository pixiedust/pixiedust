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

from pixiedust.display.streamingDisplay import StreamingDisplay
from pixiedust.display.display import CellHandshake
from pixiedust.display.chart.renderers import PixiedustRenderer
from pixiedust.utils import Logger
import pandas
import numpy as np
from bokeh.io import push_notebook, show, output_notebook
from bokeh.models import HoverTool
from bokeh.plotting import figure 
from bokeh.io import notebook_div, _state, _CommsHandle
from bokeh.util.serialization import make_id
from bokeh.util.notebook import get_comms
from pixiedust.display.streamingDisplay import *

@PixiedustRenderer(rendererId="bokeh")
@Logger()
class BokehStreamingDisplay(StreamingDisplay):
    CellHandshake.addCallbackSniffer( lambda: "{'nostore_bokeh':!!window.Bokeh}")

    def __init__(self, options, entity, dataHandler=None):
        super(BokehStreamingDisplay,self).__init__(options,entity,dataHandler)
        self.handleId = None
        self.TOOLS="crosshair,pan,wheel_zoom,box_zoom,reset,tap,box_select,lasso_select"
        self.figure = figure(tools=self.TOOLS)
        self.figure.axis.major_label_text_font_size = "18pt"
        self.hover = HoverTool(tooltips=None, mode="vline")
        self.figure.add_tools(self.hover)
        
        self.comms_handle = None
        self.glyphRenderer = None
        self.setup();
    
    def setup(self):
        pass
    
    def createGlyphRenderer(self, figure):
        return None
    
    def updateGlyphRenderer(self, figure, glyphRenderer):
        pass
    
    def _concatArrays(self,a,b):
        if type(a) != type(b):
            raise Exception("Can't concatenate objects of different types")
        if isinstance(a, list):
            return a+b
        elif isinstance(a, np.ndarray):
            return np.concatenate((a,b))
        raise Exception("Can't concatenate: unsupported types")
        
    def _delWindowElements(self, array):
        if isinstance(array, list):
            del array[:len(array)-self.windowSize]
            return array
        elif isinstance(array, np.ndarray):
            array = np.delete(array, range(0, len(array) - self.windowSize))
            return array
        raise Exception("Can't delete: unsupported type")
        
    def _toNPArray(self, a ):
        if isinstance(a, list):
            return np.array(a)
        elif isinstance(a, np.ndarray):
            return a
        raise Exception("Can't cast to np array: unsupported type")
    
    def doRender(self, handlerId):
        clientHasBokeh = self.options.get("nostore_bokeh", "false") == "true"
        if not clientHasBokeh:          
            output_notebook(hide_banner=True)
        data = self.entity.getNextData()
        if data is None:
            return
        
        x = None
        y = None
        
        if isinstance(data, (list,np.ndarray)):
            x = list(range(self.windowSize)) if self.glyphRenderer is None else self.glyphRenderer.data_source.data['x']
            y = data if self.glyphRenderer is None else self._concatArrays(self.glyphRenderer.data_source.data['y'],data)
            if len(y) < self.windowSize:
                y = [0]*(self.windowSize-len(y)) + y
            elif len(y) > self.windowSize:
                y = self._delWindowElements(y)
        elif isinstance(data, pandas.core.frame.DataFrame):
            pd = pd.drop(pd.index[[0]])
            #pd.index = list(range(len(pd.index)))
            pd['x'] = list(range(len(pd.index)))
        else:
            x = data[0]
            y = data[1]
        
        if self.glyphRenderer is None:
            self.glyphRenderer = self.createGlyphRenderer( self.figure, x, y )
        else:        
            self.updateGlyphRenderer( self.figure, self.glyphRenderer)
        
        if self.glyphRenderer is None:
            print("Error: no glyphRenderer found")
            return

        self.glyphRenderer.data_source.data['x'] = x
        self.glyphRenderer.data_source.data['y'] = y
        
        if not self.handleId:
            self.handleId = make_id()
            if self.figure not in _state.document.roots:
                _state.document.add_root(self.figure)
            activesStreamingEntities[self.getPrefix()] = self
            target = """
<div pd_refresh_rate="2000">
    <pd_script>
from pixiedust.display.streamingDisplay import *
displayHandler = activesStreamingEntities["{prefix}"]
displayHandler.render()
    </pd_script>
</div>
            <div id="target{prefix}">
            {chart}
            </div>            
            """.format(chart=notebook_div(self.figure, self.handleId), prefix=self.getPrefix())
            from IPython.display import display as ipythonDisplay, HTML
            ipythonDisplay(HTML(target))
            self.comms_handle = _CommsHandle(get_comms(self.handleId), _state.document,_state.document.to_json())
        else:
            push_notebook(handle = self.comms_handle)