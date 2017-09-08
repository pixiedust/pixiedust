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

from .baseStreamingDisplay import BokehStreamingDisplay
from pixiedust.display.chart.renderers import PixiedustRenderer
from pixiedust.utils import Logger

@PixiedustRenderer(id="lineChart", isStreaming=True)
@Logger()
class LineChartStreamingDisplay(BokehStreamingDisplay):
    def createGlyphRenderer(self, figure, x, y):
        self.i = 0
        return figure.line(x,y,color='navy', alpha=0.5, hover_line_color=None)
    
    def updateGlyphRenderer(self, figure, glyphRenderer):
        self.i +=1
        figure.title.text = str(self.i)