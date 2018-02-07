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
from pixiedust.display.chart.options.defaultOptions import DefaultOptions

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
class MapboxOptions(DefaultOptions, MapboxAccessToken):

    mapbox_default_token = "pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4M29iazA2Z2gycXA4N2pmbDZmangifQ.-g_vE53SD2WrJ6tFX7QHmA"

    def setup(self):
        DefaultOptions.setup(self)

        self.chart_options.append({
            "optid": "mapboxtoken",
            "classname": "field-width-50",
            "mapboxtoken": lambda: self.run_options.get("mapboxtoken") or self.mapbox_default_token,
            "widget": "mapboxAccessToken"
        })

        self.new_options["mapboxtoken"] = self.run_options.get("mapboxtoken") or self.mapbox_default_token

    def key_fields_type(self):
        return ['string', 'numeric']

    def value_fields_type(self):
        return ['any']
