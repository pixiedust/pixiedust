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
from collections import OrderedDict
from pixiedust.display.chart.renderers import PixiedustRenderer
from pixiedust.display.chart.renderers.baseChartDisplay import commonChartOptions
from pixiedust.utils import Logger
from .brunelBaseDisplay import BrunelBaseDisplay

@PixiedustRenderer(id="mapView")
@Logger()
class MapRenderer(BrunelBaseDisplay):

    def __init__(self, options, entity, dataHandler=None):
        super(MapRenderer, self).__init__(options, entity, dataHandler)
        self.types = OrderedDict([
            ('Map', {'handler': self.compute_for_map}),
            ('Heat Map', {'handler': self.compute_for_heatmap}),
            ('Tree Map', {'handler': self.compute_for_treemap}),
            ('Chord', {'handler': self.compute_for_chord}),
        ])

    @commonChartOptions
    def getChartOptions(self):
        return [
            {
                'name': 'brunelMapType',
                'description': 'Type',
                'refresh': False,
                'metadata': {
                    'type': 'dropdown',
                    'values': list(self.types.keys()),
                    'default': list(self.types.keys())[0]
                }
            }
        ]

    def compute_brunel_magic(self):
        map_type = self.options.get('brunelMapType', list(self.types.keys())[0])
        handler = self.types.get(map_type, list(self.types.values())[0]).get('handler')
        return handler()

    def compute_for_map(self):
        parts = ['map']
        parts.append("key({0}) label({0})".format(",".join(self.getKeyFields())))
        parts.append("color({})".format(",".join(self.getValueFields())))
        return parts

    def compute_for_heatmap(self):
        parts = []
        parts.append("x({})".format(",".join(self.getKeyFields())))
        parts.append("y({})".format(",".join(self.getValueFields())))
        parts.append("color(#count)")
        parts.append("style('symbol:rect; size:100%; stroke:none')")
        parts.append("sort(#count)")
        return parts
    
    def compute_for_treemap(self):
        parts = ['treemap']
        parts.append("x({0})".format(",".join(self.getKeyFields())))
        parts.append("color({0}) size({0}) label({0})".format(",".join(self.getValueFields())))
        return parts
    
    def compute_for_chord(self):
        parts = ['chord']
        parts.append("x({})".format(",".join(self.getKeyFields())))
        parts.append("y({})".format(",".join(self.getValueFields())))
        parts.append("color(#count)")
        parts.append("tooltip(#all)")
        return parts 