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

from .baseChartDisplay import BaseChartDisplay
    
class MapChartDisplay(BaseChartDisplay):

    def supportsKeyFieldLabels(self, handlerId):
        return False

    def supportsLegend(self, handlerId):
        return False
    
    def getPreferredDefaultValueFieldCount(self, handlerId):
		return 1

    def getDefaultKeyFields(self, handlerId, aggregation):
        fields = self._getDefaultKeyFields()
        if (len(fields) > 0):
            return fields
        else:
            return super(MapChartDisplay, self).getDefaultKeyFields(handlerId, aggregation) # no relevant fields found - defer to superclass
    
    def getChartContext(self, handlerId):
        return ('mapChartOptionsDialogBody.html', {})
    
    def canRenderChart(self, handlerId, aggregation, fieldNames):
        keyFields = self.options.get("keyFields")
        if ((keyFields is not None and len(keyFields) > 0) or len(self._getDefaultKeyFields()) > 0):
            return (True, None)
        else:
            return (False, "No location field found ('country', 'province', 'state', 'city', or 'latitude'/'longitude').<br>Use the Chart Options dialog to specify a location field.")

    def doRenderChart(self, handlerId, dialogTemplate, dialogOptions, aggregation, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues):
        latLong = super(MapChartDisplay, self).isNumericField(keyFields[0])
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
        if self.options["mapRegion"] == "US":
            self.options["mapResolution"] = "provinces"
        else:
            self.options["mapResolution"] = "countries"
        dialogBody = self.renderTemplate(dialogTemplate, **dialogOptions)
        mapData = "[["
        for i, keyField in enumerate(keyFields):
            if i is not 0:
                mapData = mapData + ", "
            mapData = mapData + "'" + keyFields[0].replace('"','') + "'"
        for i, valueField in enumerate(valueFields):
            mapData = mapData + ", '" + valueField.replace('"','') + "'"
        mapData = mapData + "]"
        for i, keyFieldLabel in enumerate(keyFieldLabels):
            mapData = mapData + ", ["
            if latLong == False:
                mapData = mapData + "'"
            mapData = mapData + keyFieldLabels[i].replace('"','')
            if latLong == False:
                 mapData = mapData + "'"
            for j, valueFieldValue in enumerate(valueFieldValues):
                mapData = mapData + ", " + str(valueFieldValues[j][i]).replace('"','')
            mapData = mapData + "]"
        mapData = mapData + "]"
        self.options["mapData"] = mapData.replace("'",'"')
        self._addScriptElement("https://www.gstatic.com/charts/loader.js")
        self._addScriptElement("https://www.google.com/jsapi", callback=self.renderTemplate("mapChart.js"))
        self._addHTMLTemplate("mapChart.html", optionsDialogBody=dialogBody)

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