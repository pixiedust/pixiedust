# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2018
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

from pixiedust.display.app import *
from pixiedust.utils import Logger
from pixiedust.display.chart.options.optionsShell import *
from pixiedust.display.chart.options.components.AggregationSelector import *
from pixiedust.display.chart.options.components.RowCount import *
import six

@Logger()
class GeoSelector(object):
    @route(widget="pdGeoSelector")
    def chart_option_geo_widget(self, optid, lonField, latField, valueFields, extraFields):
        self.lonField = lonField
        self.latField = latField
        self.lonFieldNames = ["x","lon","long","longitude"]
        self.latFieldNames = ["y","lat","latitude"]
        self.valueFields = valueFields.split(",") if isinstance(valueFields, six.string_types) and valueFields else valueFields or []
        self.extraFields = extraFields.split(",") if isinstance(extraFields, six.string_types) and extraFields else extraFields or []
        self.valueFieldsType = self.value_fields_type()
        self.extraFieldsType = self.extra_fields_type()
        self._addHTMLTemplate("geoselector.html")

    def key_fields_supported(self):
        return self.get_renderer.supportsKeyFields(self.parsed_command['kwargs']['handlerId'])

    def value_fields_type(self):
        return ['numeric']

    def extra_fields_type(self):
        return ['numeric','string']

@Logger()
class MapboxAccessToken(object):
    @route(widget="mapboxAccessToken")
    def mapbox_access_token_widget(self, optid, mapboxtoken):
        return """
            <div class="form-group">
            <label for="mapboxoption{{optid}}{{prefix}}">
                <a href="https://www.mapbox.com/help/create-api-access-token/" target="_mapboxwin">Mapbox Access Token</a>: <i class="fa fa-question-circle" title="Get a Mapbox access token by creating a free account at mapbox.com"></i>
            </label>
            <input type="text" class="form-control" id="mapboxoption{{optid}}{{prefix}}" name="{{optid}}" value="{{mapboxtoken}}"
                pd_script="self.options_callback('{{optid}}', '$val(mapboxoption{{optid}}{{prefix}})')" onkeyup="$(this).trigger('click');">
            </div>
            """

@PixieApp
@Logger()
class MapboxOptions(OptionsShell, GeoSelector, AggregationSelector, RowCount, MapboxAccessToken):

    mapbox_default_token = "pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4M29iazA2Z2gycXA4N2pmbDZmangifQ.-g_vE53SD2WrJ6tFX7QHmA"

    def setup(self):
        OptionsShell.setup(self)

        self.chart_options.append({
            "optid": "keyvalue",
            "classname": "no_loading_msg",
            "lonField": lambda: self.run_options.get("lonField") or "",
            "latField": lambda: self.run_options.get("latField") or "",
            "valueFields": lambda: self.run_options.get("valueFields") or "",
            "extraFields": lambda: self.run_options.get("extraFields") or "",
            "widget": "pdGeoSelector"
        })

        if self.aggregation_supported():
            self.chart_options.append({
                "optid": "aggregation",
                "classname": "field-width-50 no_loading_msg",
                "aggregation": lambda: self.run_options.get("aggregation") or "",
                "widget": "pdAggregationSelector"
            })

        self.chart_options.append({
            "optid": "rowCount",
            "classname": "field-width-50 no_loading_msg",
            "count": lambda: self.run_options.get("rowCount") or 100,
            "widget": "pdRowCount"
        })

        self.chart_options.append({
            "optid": "mapboxtoken",
            "classname": "field-width-50",
            "mapboxtoken": lambda: self.run_options.get("mapboxtoken") or self.mapbox_default_token,
            "widget": "mapboxAccessToken"
        })

        self.new_options["mapboxtoken"] = self.run_options.get("mapboxtoken") or self.mapbox_default_token

    def options_callback(self, option, value):
        self.new_options[option] = value
        if option is 'latField' or option is 'lonField':
          if 'keyFields' not in self.new_options or len(self.new_options['keyFields']) == 0:
              self.new_options['keyFields'] = value  
          elif option not in self.new_options['keyFields']:
              self.new_options['keyFields'] += ',' + value

    def aggregation_supported(self):
        return self.get_renderer.supportsAggregation(self.parsed_command['kwargs']['handlerId'])

    def value_fields_type(self):
        return ['any']

    def extra_fields_type(self):
        return ['any']
