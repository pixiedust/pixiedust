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
from pixiedust.utils import cache
from pixiedust.utils import Logger
import json 

@PixiedustRenderer(id="mapView")
@Logger()
class MapViewDisplay(MapBoxBaseDisplay):
    def isMap(self, handlerId):
        return True

    def supportsAggregation(self, handlerId):
        return True

    def getDefaultAggregation(self, handlerId):
        return "SUM"

    def supportsLegend(self, handlerId):
        return True

    def getPreferredDefaultKeyFieldCount(self, handlerId):
        return 2

    def getPreferredDefaultValueFieldCount(self, handlerId):
        return 1

    def canRenderChart(self):
        keyFields = self.getKeyFields()
        if ((keyFields is not None and len(keyFields) > 0) or len(self._getDefaultKeyFields()) > 0):
            return (True, None)
        else:
            return (False, "No location field found ('latitude'/'longitude', 'lat/lon', 'y/x').<br>Use the Chart Options dialog to specify location fields.")

    def getChartContext(self, handlerId):
        diagTemplate = MapBoxBaseDisplay.__module__ + ":mapViewOptionsDialogBody.html"
        return (diagTemplate, {})
    
    def doRenderChart(self):
        mbtoken = self.options.get("mapboxtoken")
        if not mbtoken or len(mbtoken)<5:
            return self.renderTemplate("noaccesstoken.html")

        df = self.getWorkingPandasDataFrame()

        keyFields = self.getKeyFields()
        lonFieldIdx = 0
        latFieldIdx = 1
        if keyFields[0] == self.getLatField(): 
            lonFieldIdx = 1
            latFieldIdx = 0
        valueFields = self.getValueFields()
        valueFieldIdxs = []
        for j, valueField in enumerate(valueFields):
            valueFieldIdxs.append(df.columns.get_loc(valueField))
        

        min = [df[keyFields[lonFieldIdx]].min(), df[keyFields[latFieldIdx]].min()]
        max = [df[keyFields[lonFieldIdx]].max(), df[keyFields[latFieldIdx]].max()]

        # Transform the data into GeoJSON for use in the Mapbox client API
        pygeojson = {'type':'FeatureCollection', 'features':[]}

        for row in df.itertuples():
            feature = {'type':'Feature',
                        'properties':{},
                        'geometry':{'type':'Point',
                                    'coordinates':[]}}
            feature['geometry']['coordinates'] = [row[lonFieldIdx+1], row[latFieldIdx+1]]
            for idx, valueFieldIdx in enumerate(valueFieldIdxs):
                feature['properties'][valueFields[idx]] = row[valueFieldIdx+1]
            pygeojson['features'].append(feature)

        self.options["mapBounds"] = json.dumps([min,max])
        self.options["mapData"] = json.dumps(pygeojson)

        paint = {'circle-radius':12,'circle-color':'#ff0000'}
        bins = []

        if len(valueFields) > 0:
            mapValueField = valueFields[0]
            self.options["mapValueField"] = mapValueField

        if not self.options.get("kind"): 
            self.options["kind"] = "choropleth"
        # if there's a numeric value field paint the data as a choropleth map
        if self.options.get("kind") != "simple" and len(valueFields) > 0:
            minval = df[valueFields[0]].min()
            maxval = df[valueFields[0]].max()
            bins = [ (minval,'#ffffcc'), (df[valueFields[0]].quantile(0.25),'#a1dab4'), (df[valueFields[0]].quantile(0.5),'#41b6c4'), (df[valueFields[0]].quantile(0.75),'#2c7fb8'), (maxval,'#253494') ]
            paint['circle-opacity'] = 0.85
            paint['circle-color'] = {"property":mapValueField}
            paint['circle-color']['stops'] = []
            for bin in bins: 
                paint['circle-color']['stops'].append( [bin[0], bin[1]] )
        self.options["mapStyle"] = json.dumps(paint)
        w = self.getPreferredOutputWidth()
        h = self.getPreferredOutputHeight()
        body = self.renderTemplate("mapView.html", bins=bins, prefwidth=w, prefheight=h)
        return self.renderTemplate("iframesrcdoc.html", body=body, prefwidth=w, prefheight=h)

    def isLatLonChart(self):
        llnames = ['lat','latitude','y','lon','long','longitude','x']
        isll = True;
        keyFields = self.getKeyFields()
        if ((keyFields is not None) and len(keyFields) == 2):
            for field in keyFields:
                if field.lower() not in llnames:
                    isll = False
        return isll;

    def getLatField(self):
        names = ['lat','latitude','y']
        keyFields = self.getKeyFields()
        if (keyFields is not None):
            for field in keyFields:
                if field.lower() in names:
                    return field
        return None;

    def getLonField(self):
        names = ['lon','long','longitude','x']
        keyFields = self.getKeyFields()
        if (keyFields is not None):
            for field in keyFields:
                if field.lower() in names:
                    return field
        return None;

    def _getDefaultKeyFields(self):
        # check for lat/long
        latLongFields = []
        for field in self.entity.schema.fields:
            if field.name.lower() == 'lat' or field.name.lower() == 'latitude' or field.name.lower() == 'y':
                latLongFields.append(field.name)
        for field in self.entity.schema.fields:
            if field.name.lower() == 'lon' or field.name.lower() == 'long' or field.name.lower() == 'longitude' or field.name.lower() == 'x':
                latLongFields.append(field.name)
        if (len(latLongFields) == 2):
            return latLongFields
        # if we get here, look for an address field
        for field in self.entity.schema.fields:
            if field.name.lower() == 'address':
                return latLongFields.append(field.name)
        return []
