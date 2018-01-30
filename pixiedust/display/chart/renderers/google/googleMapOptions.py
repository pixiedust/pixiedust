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
class GoogleMapApiKey(object):
    @route(widget="googleMapApiKey")
    def google_map_api_key(self, optid, googlemapapikey):
        return """
<div class="form-group">
  <label for="googlemapoption{{optid}}{{prefix}}">
    <a href="https://support.google.com/googleapi/answer/6158862?hl=en&ref_topic=7013279" target="_blank">Google Maps API Key</a>: <i class="fa fa-question-circle" title="Get a Google Maps API key by accessing the Google API Console"></i>
  </label>
  <input type="text" class="form-control" id="googlemapoption{{optid}}{{prefix}}" name="{{optid}}" value="{{googlemapapikey}}"
    pd_script="self.options_callback('{{optid}}', '$val(googlemapoption{{optid}}{{prefix}})')" onkeyup="$(this).trigger('click');">
</div>
"""

@PixieApp
@Logger()
class GoogleMapOptions(DefaultOptions, GoogleMapApiKey):
    def setup(self):
        DefaultOptions.setup(self)

        self.chart_options.append({
            "optid": "googlemapapikey",
            "classname": "field-width-50",
            "googlemapapikey": lambda: self.options.get("googlemapapikey") or "",
            "widget": "googleMapApiKey"
        })

    def key_fields_type(self):
        return ['string', 'numeric']

    def value_fields_type(self):
        return ['any']
