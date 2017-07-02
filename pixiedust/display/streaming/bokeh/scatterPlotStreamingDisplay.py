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
from ..bokeh import BokehStreamingDisplay
import numpy as np

N=100
class ScatterPlotStreamingDisplay(BokehStreamingDisplay):
    def createGlyphRenderer(self, figure, x, y):
        self.radii = np.random.random(size=N) * 2
        self.colors = ["#%02x%02x%02x" % (int(r), int(g), 150) for r, g in zip(50+2*self._toNPArray(x), 30+2*self._toNPArray(y))]
        self.i = 0
        return figure.circle(x,y, radius=self.radii, 
                fill_color=self.colors, fill_alpha=0.6, line_color=None, 
                hover_fill_color="black", hover_fill_alpha=0.7, hover_line_color=None)
        
    def updateGlyphRenderer(self, figure, glyphRenderer):
        self.i +=1 
        figure.title.text = str(self.i)    
        glyphRenderer.data_source.data['radius'] = self.radii * (2 + np.sin(self.i/5))