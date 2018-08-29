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
from pixiedust.utils.shellAccess import ShellAccess
from pixiedust.display.streamingDisplay import *
import json
import numpy
import geojson
import uuid
import requests

def defaultJSONEncoding(o):
    if isinstance(o, numpy.integer): 
        return int(o)
    raise TypeError

@PixiedustRenderer(id="mapView")
@Logger()
class MapViewDisplay(MapBoxBaseDisplay):
    def isMap(self, handlerId):
        return True

    def supportsAggregation(self, handlerId):
        return False

    def supportsLegend(self, handlerId):
        return True

    def getPreferredDefaultKeyFieldCount(self, handlerId):
        return 2

    def getPreferredDefaultValueFieldCount(self, handlerId):
        return 1

    def getLatField(self):
        latf = self.options.get("latField")
        if latf is not None:
            return latf
        # @deprecated support for old metadata
        names = ['lat','latitude','y']
        keyFields = self.getKeyFields()
        if (keyFields is not None):
            for field in keyFields:
                if field.lower() in names:
                    return field
        return None;

    def getLonField(self):
        lonf = self.options.get("lonField")
        if lonf is not None:
            return lonf
        # @deprecated support for old metadata
        names = ['lon','long','longitude','x']
        keyFields = self.getKeyFields()
        if (keyFields is not None):
            for field in keyFields:
                if field.lower() in names:
                    return field
        return None;

    def canRenderChart(self):
        lonf = self.getLonField()
        latf = self.getLatField()
        if lonf is None or latf is None:
            return (False, "Required location fields not found ('latitude'/'longitude', 'lat/lon', 'y/x').<br>Use the Chart Options dialog to specify location fields.")
        return (True, None)

    def doRenderChart(self):
        mbtoken = self.options.get("mapboxtoken")
        if not mbtoken:
            return self.renderTemplate("noaccesstoken.html")
        else:
            self.response = requests.get("https://api.mapbox.com/tokens/v2?access_token=" + mbtoken)
            if (self.response.status_code == 200 and self.response.json()['code'] != 'TokenValid') \
                    or self.response.status_code != 200:
                return self.renderTemplate("tokenerror.html")

        body = self.renderMapView(mbtoken)
        if self.isStreaming:
            self.commId = str(uuid.uuid4())
            activesStreamingEntities[self.options.get("cell_id")] = self.entity

        return self.renderTemplate("iframesrcdoc.html", body=body, prefwidth=self.getPreferredOutputWidth(), prefheight=self.getPreferredOutputHeight())

    ## overrides empty method in baseChartDisplay
    def getExtraFields(self):
        fieldNames = self.getFieldNames()
        if len(fieldNames) == 0:
            return []
        extraFields = []
        extraFieldStr = self.options.get("extraFields")
        if extraFieldStr is not None:
            extraFields = extraFieldStr.split(",")
            extraFields = [val for val in extraFields if val in fieldNames]
        return extraFields

    def renderMapView(self, mbtoken):

        # generate a working pandas data frame using the fields we need
        df = self.getWorkingPandasDataFrame()
        lonField = self.getLonField()
        latField = self.getLatField()

        # geomType can be either 0: (Multi)Point, 1: (Multi)LineString, 2: (Multi)Polygon
        geomType = 0
        bins = []

        # cast to double just in case the fields are strings
        min = [ numpy.double(df[lonField]).min(), numpy.double(df[latField]).min() ]
        max = [ numpy.double(df[lonField]).max(), numpy.double(df[latField]).max() ]
        self.options["mapBounds"] = json.dumps([min,max], default=defaultJSONEncoding)

        valueFields = self.getValueFields()
        
        #check if we have a extra fields for get info clicks
        extraFields = self.options.get("extraFields", None)
        if extraFields is not None and len(extraFields) < 1:
            extraFields = None
        extraFields = [a for a in extraFields.split(",") if a not in valueFields] if extraFields is not None else []

        # calculate indexes of all fields
        valueFieldIdxs = []
        allProps = valueFields + extraFields
        for j, valueField in enumerate( allProps ):
            valueFieldIdxs.append(df.columns.get_loc(valueField))

        # Transform the data into GeoJSON for use in the Mapbox client API
        features = []
        for index,row in df.iterrows():
            feature = {'type':'Feature',
                        'properties':{},
                        'geometry':{'type':'Point',
                                    'coordinates':[]}}
            
            if geomType == 0:
                feature['geometry']['coordinates'] = [ row[lonField], row[latField] ]
            # only points are supported
                
            for idx, valueFieldIdx in enumerate(valueFieldIdxs):
                feature['properties'][allProps[idx]] = row[valueFieldIdx]
            features.append(feature)

        if len(features)>0:
            pygeojson = {'type':'FeatureCollection', 'features':features}
            self.options["mapData"] = json.dumps(pygeojson,default=defaultJSONEncoding)

            # Now let's figure out whether we have Line or Polygon data, if it wasn't already found to be Point
            if geomType != 1:
                if features[0]['geometry']['type'].endswith('LineString'):
                    geomType = 1
                elif features[0]['geometry']['type'].endswith('Polygon'):
                    geomType = 2
                else:
                    geomType = -1
                
            #### build up the map style

            # basic color
            paint = {}
            if geomType == 1:
                paint['line-color'] = '#ff0000'
                paint['line-width'] = 2
                if self.options.get("coloropacity"):
                    paint['line-opacity'] = float(self.options.get("coloropacity")) / 100
            elif geomType == 2:
                paint['fill-color'] = '#ff0000'
                paint['fill-opacity'] = 0.50
                if self.options.get("coloropacity"):
                    paint['fill-opacity'] = float(self.options.get("coloropacity")) / 100
            else:
                paint['circle-radius'] = 12
                paint['circle-color'] = '#ff0000'
                paint['circle-opacity'] = 0.50
                if self.options.get("coloropacity"):
                    paint['circle-opacity'] = float(self.options.get("coloropacity")) / 100
                if (self.options.get("kind") and self.options.get("kind").find("cluster") >= 0):
                    paint['circle-opacity'] = 1.0

            if len(valueFields) > 0:
                mapValueField = valueFields[0]
                self.options["mapValueField"] = mapValueField

            if not self.options.get("kind"): 
                self.options["kind"] = "choropleth-cluster"

            # if there's a numeric value field and type is not 'simple', paint the data as a choropleth map
            if self.options.get("kind") and self.options.get("kind").find("simple") < 0 and len(valueFields) > 0:
                # color options
                bincolors = []
                bincolors.append(['#ffffcc','#a1dab4','#41b6c4','#2c7fb8','#253494']) #yellow to blue
                bincolors.append(['#fee5d9','#fcae91','#fb6a4a','#de2d26','#a50f15']) #reds
                bincolors.append(['#f7f7f7','#cccccc','#969696','#636363','#252525']) #grayscale
                bincolors.append(['#e66101','#fdb863','#f7f7f7','#b2abd2','#5e3c99']) #orange to purple (diverging values)

                bincolorsIdx = 0
                if self.options.get("colorrampname"):
                    if self.options.get("colorrampname") == "Light to Dark Red":
                        bincolorsIdx = 1
                    if self.options.get("colorrampname") == "Grayscale":
                        bincolorsIdx = 2
                    if self.options.get("colorrampname") == "Orange to Purple":
                        bincolorsIdx = 3

                minval = df[valueFields[0]].min()
                maxval = df[valueFields[0]].max()
                bins.append((minval,bincolors[bincolorsIdx][0]))
                bins.append((df[valueFields[0]].quantile(0.25),bincolors[bincolorsIdx][1]))
                bins.append((df[valueFields[0]].quantile(0.5),bincolors[bincolorsIdx][2]))
                bins.append((df[valueFields[0]].quantile(0.75),bincolors[bincolorsIdx][3]))
                bins.append((maxval,bincolors[bincolorsIdx][4]))

                if geomType == 1:
                    # paint['line-opacity'] = 0.65
                    paint['line-color'] = {"property":mapValueField}
                    paint['line-color']['stops'] = []
                    for bin in bins:
                        paint['line-color']['stops'].append([bin[0], bin[1]])
                elif geomType == 2:
                    paint['fill-color'] = {"property":mapValueField}
                    paint['fill-color']['stops'] = []
                    for bin in bins:
                        paint['fill-color']['stops'].append([bin[0], bin[1]])
                else:
                    # paint['circle-opacity'] = 0.65
                    paint['circle-color'] = {"property":mapValueField}
                    paint['circle-color']['stops'] = []
                    for bin in bins: 
                        paint['circle-color']['stops'].append([bin[0], bin[1]])
                    paint['circle-radius'] = 12


            self.options["mapStyle"] = json.dumps(paint,default=defaultJSONEncoding)
            
        w = self.getPreferredOutputWidth()
        h = self.getPreferredOutputHeight()

        # handle custom layers
        userlayers = []
        l = (ShellAccess,ShellAccess) 
        papp = self.options.get("nostore_pixieapp")
        if papp is not None and ShellAccess[papp] is not None:
            l = (ShellAccess[papp], dir(ShellAccess[papp]))
        for key in [a for a in l[1] if not callable(getattr(l[0], a)) and not a.startswith("_")]:
            v = getattr(l[0],key)            
            if isinstance(v, dict) and "maptype" in v and v["maptype"].lower() == "mapbox" and "source" in v and "type" in v["source"] and v["source"]["type"] == "geojson" and "id" in v and "data" in v["source"]:
                gj = geojson.loads(json.dumps(v["source"]["data"]))
                isvalid = True
                if hasattr(geojson, "is_valid"): # then we're using old version of geojson module
                    isvalid = geojson.is_valid(gj)["valid"] == "yes"
                    self.debug("IN hasattr(geojson,is_valid). Validity is "+str(isvalid))
                else: # we're using a newer version of geojson module
                    isvalid = gj.is_valid
                if isvalid:
                    userlayers.append(v)
                else:
                    self.debug("Invalid GeoJSON: {0}".format(str(v["source"]["data"])))
        self.debug("userlayers length: "+str(len(userlayers)))
        # end handle custom layers

        uniqueid = str(uuid.uuid4())[:8]
        return self.renderTemplate("mapView.html", bins=bins, userlayers=userlayers, prefwidth=w, prefheight=h, randomid=uniqueid)

    def isLatLonChart(self):
        llnames = ['lat','latitude','y','lon','long','longitude','x']
        if self.getLonField() is None or self.getLonField() not in llnames or self.getLatField() is None or self.getLatField() not in llnames:
            return False
        return True;
