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
from pixiedust.display.chart.options.optionsShell import OptionsShell
from pixiedust.display.chart.options.components.BinQuantiles import BinQuantiles

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

class MapboxCustomBaseColor(object):
    @route(widget="mapboxCustomBaseColor")
    def mapbox_color_picker_widget(self, optid, custombasecolor, labelname="Custom Base Color:"):
        return """
<div class="form-group">
<label for="mapboxoption{{optid}}{{prefix}}">{{labelname}}</label>
<input type="color" class="form-control" id="mapboxoption{{optid}}{{prefix}}" name="{{optid}}" value="{{custombasecolor}}"
  pd_script="self.options_callback('{{optid}}', '$val(mapboxoption{{optid}}{{prefix}})')" onkeyup="$(this).trigger('click');">
</div>
"""

@PixieApp
@Logger()
class MapboxOptions(DefaultOptions, MapboxAccessToken, MapboxCustomBaseColor):

    mapbox_default_token = "pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4M29iazA2Z2gycXA4N2pmbDZmangifQ.-g_vE53SD2WrJ6tFX7QHmA"

    def setup(self):
        DefaultOptions.setup(self)

        self.chart_options.append({
            "optid": "mapboxtoken",
            "classname": "field-width-50",
            "mapboxtoken": lambda: self.run_options.get("mapboxtoken") or self.mapbox_default_token,
            "widget": "mapboxAccessToken"
        })

        self.chart_options.append({
            "optid": "custombasecolor",
            "classname": "field-width-50",
            "custombasecolor": lambda: self.run_options.get("custombasecolor") or "#ff0000",
            "labelname": "Custom Base Color:",
            "widget": "mapboxCustomBaseColor"
        })

        self.chart_options.append({
            "optid": "custombasecolorsecondary",
            "classname": "field-width-50",
            "custombasecolor": lambda: self.run_options.get("custombasecolorsecondary") or "#ff0000",
            "labelname": "Secondary Custom Base Color:",
            "widget": "mapboxCustomBaseColor"
        })

        self.new_options["mapboxtoken"] = self.run_options.get("mapboxtoken") or self.mapbox_default_token

    def key_fields_type(self):
        return ['string', 'numeric']

    def value_fields_type(self):
        return ['any']

@PixieApp
@Logger()
class NumBinsOptions(OptionsShell, BinQuantiles):

    def setup(self):
        OptionsShell.setup(self)
        # should only be one entry in the chart option list for chart name
        # don't want that, just get rid of it
        self.chart_options.pop()

        numbins = int(self.run_options.get("numbins") or 5)
        self.setupQuantiles(numbins)

        self.chart_options.append({
            "optid": "binRanges",
            "classname": "field-width-100 no_loading_msg",
            "numbins": numbins,
            "quantiles": self.new_options["quantiles"],
            "widget": "pdBinQuantiles"
        })

    # default equal size quantiles
    # for numBins=5, quantiles are 0, 0.25, 0.50, 0.75, 1
    def generateQuantiles(self, numBins):
        quantiles = []
        for i in range(numBins):
            quantiles.append(float(i)/(numBins-1.0))
        return ",".join(map(str,quantiles))

    # set up quantiles based on numbins/presence of quantiles string in metadata
    def setupQuantiles(self, numBins):
        if self.run_options.get("quantiles"):
            if len(self.run_options["quantiles"].split(",")) == numBins:
                self.new_options["quantiles"] = self.run_options["quantiles"]
                return

        self.new_options["quantiles"] = self.generateQuantiles(numBins)
        return
