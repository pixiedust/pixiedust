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
from .mapBoxBaseDisplay import MapBoxBaseDisplay

import pixiedust

myLogger = pixiedust.getLogger(__name__)

@PixiedustRenderer(id="mapView")
class MapViewDisplay(MapBoxBaseDisplay):
    def doRenderChart(self):
        # return "<br/><b>Map view powered by MapBox not yet implemented</b><br/><br/>"
        geojs = {
            'type':'Feature', 
            'properties': {
                'name': 'Philadelphia', 
                'pop': 6000000
            }, 
            'geometry': {
                'type': 'Point', 
                'coordinates': [102.0, 0.5]
            }
        }
        self.options["mapData"] = geojs
        self.options["mapbox_token"] = 'pk.eyJ1IjoicmFqcnNpbmdoIiwiYSI6ImpzeDhXbk0ifQ.VeSXCxcobmgfLgJAnsK3nw'
        self._addScriptElement("https://api.mapbox.com/mapbox-gl-js/v0.31.0/mapbox-gl.js", callback=self.renderTemplate("mapView.js"))
        return self.renderTemplate("mapView.html")

    def df_to_geojson(df, properties, lat='latitude', lon='longitude'):
        geojson = {'type':'FeatureCollection', 'features':[]}
        for _, row in df.iterrows():
            feature = {'type':'Feature',
                        'properties':{},
                        'geometry':{'type':'Point',
                                    'coordinates':[]}}
            feature['geometry']['coordinates'] = [row[lon],row[lat]]
            for prop in properties:
                feature['properties'][prop] = row[prop]
            geojson['features'].append(feature)
        return geojson
