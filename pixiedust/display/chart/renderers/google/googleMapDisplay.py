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
from .googleBaseDisplay import GoogleBaseDisplay

import numpy as np
import pixiedust

myLogger = pixiedust.getLogger(__name__)

@PixiedustRenderer(id="mapView")
class MapViewDisplay(GoogleBaseDisplay):

    def supportsKeyFieldLabels(self, handlerId):
        return False
    
    def getPreferredDefaultValueFieldCount(self, handlerId):
        return 1

    def getDefaultKeyFields(self, handlerId, aggregation):
        fields = self._getDefaultKeyFields()
        if (len(fields) > 0):
            return fields
        else:
            return super(MapViewDisplay, self).getDefaultKeyFields(handlerId, aggregation) # no relevant fields found - defer to superclass
    
    def getChartContext(self, handlerId):
        diagTemplate = GoogleBaseDisplay.__module__ + ":mapViewOptionsDialogBody.html"
        return (diagTemplate, {})
    
    def canRenderChart(self):
        keyFields = self.getKeyFields()
        if ((keyFields is not None and len(keyFields) > 0) or len(self._getDefaultKeyFields()) > 0):
            return (True, None)
        else:
            return (False, "No location field found ('country', 'province', 'state', 'city', or 'latitude'/'longitude').<br>Use the Chart Options dialog to specify a location field.")

    def doRenderChart(self):
        keyFields = self.getKeyFields()
        # keyFieldLabels = self.getKeyFieldLabels()
        valueFields = self.getValueFields()
        latLong = self.dataHandler.isNumericField(keyFields[0])
        apikey = self.options.get("googlemapapikey")

        if self.options.get("mapRegion") is None:
            if keyFields[0].lower() == "state":
                self.options["mapRegion"] = "US"
            else:    
                self.options["mapRegion"] = "world"

        if self.options.get("mapDisplayMode") is None:
            if latLong:
                self.options["mapDisplayMode"] = "markers"
            else:
                self.options["mapDisplayMode"] = "region"

        if self.options.get("mapDisplayMode") != "region" and (apikey is None or len(apikey)<5):
            return self.renderTemplate("noapikey.html")
            
        if self.options["mapRegion"] == "US":
            self.options["mapResolution"] = "provinces"
        else:
            self.options["mapResolution"] = "countries"

        df = self.getWorkingPandasDataFrame()
        colData = str(df.columns.values.tolist())
        valData = str(df.values.tolist()).encode('utf-8')
        mapData = "[" + valData.replace('[', (colData + ", "), 1)

        self.options["mapData"] = mapData.replace("'",'"').replace('[u"', '["').replace(', u"', ', "')
        self._addScriptElement("https://www.gstatic.com/charts/loader.js")
        if apikey is not None and len(apikey)>5:
            self._addScriptElement("https://maps.googleapis.com/maps/api/js?key={0}".format(apikey))
        self._addScriptElement("https://www.google.com/jsapi", callback=self.renderTemplate("mapView.js"))
        return self.renderTemplate("mapView.html")

    def _getDefaultKeyFields(self):
        for field in self.entity.schema.fields:
            if field.name.lower() == 'country' or field.name.lower() == 'province' or field.name.lower() == 'state' or field.name.lower() == 'city':
                return [field.name]
        # check for lat/long
        latLongFields = []
        for field in self.entity.schema.fields:
            if field.name.lower() == 'lat' or field.name.lower() == 'latitude':
                latLongFields.append(field.name)
        for field in self.entity.schema.fields:
            if field.name.lower() == 'lon' or field.name.lower() == 'long' or field.name.lower() == 'longitude':
                latLongFields.append(field.name)
        if (len(latLongFields) == 2):
            return latLongFields
        return []
