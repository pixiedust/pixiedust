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
        useLatLong = False
        for field in self.entity.schema.fields:
            if field.name.lower() == 'country' or field.name.lower() == 'province' or field.name.lower() == 'state' or field.name.lower() == 'city':
                return [field.name]
        # no field found - defer to superclass
        return super(MapChartDisplay, self).getDefaultKeyFields(handlerId, aggregation)
    
    def getChartContext(self, handlerId):
        return ('mapChartOptionsDialogBody.html', {})
    
    def doRenderChart(self, handlerId, dialogTemplate, dialogOptions, aggregation, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues):
        if self.options.get("mapRegion") is None:
            if keyFields[0].lower() == "state":
                self.options["mapRegion"] = "US"
            else:    
                self.options["mapRegion"] = "world"
        if self.options.get("mapDisplayMode") is None:
            self.options["mapDisplayMode"] = "region"
        dialogBody = self.renderTemplate(dialogTemplate, **dialogOptions)
        mapData = "[['" + keyFields[0].replace('"','') + "'"
        for i, valueField in enumerate(valueFields):
            mapData = mapData + ", '" + valueField.replace('"','') + "'"
        mapData = mapData + "]"
        for i, keyFieldLabel in enumerate(keyFieldLabels):
            mapData = mapData + ", ['" + keyFieldLabels[i].replace('"','') + "'"
            for j, valueFieldValue in enumerate(valueFieldValues):
                mapData = mapData + ", " + str(valueFieldValues[j][i]).replace('"','')
            mapData = mapData + "]"
        mapData = mapData + "]"
        self.options["mapData"] = mapData.replace("'",'"')
        self._addScriptElement("https://www.gstatic.com/charts/loader.js")
        self._addScriptElement("https://www.google.com/jsapi", callback=self.renderTemplate("mapChart.js", body=dialogBody))
        self._addHTMLTemplate("mapChart.html")