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

from pixiedust.display.chart.renderers import PixiedustRenderer
from ..baseChartDisplay import BaseChartDisplay
from six import with_metaclass
from abc import ABCMeta

import pixiedust

myLogger = pixiedust.getLogger(__name__)

@PixiedustRenderer(rendererId="google")
class GoogleBaseDisplay(with_metaclass(ABCMeta, BaseChartDisplay)):
    def get_options_dialog_pixieapp(self):
        """
        Return the fully qualified path to a PixieApp used to display the dialog options
        PixieApp must inherit from pixiedust.display.chart.options.baseOptions.BaseOptions
        """
        return "pixiedust.display.chart.renderers.google.googleMapOptions.GoogleMapOptions"

    def getChartOptions(self):
        return [
            {
                'name': 'chartsize',
                'description': 'Map Size',
                'metadata': {
                    'type': 'slider',
                    'max': 100,
                    'min': 50,
                    'default': 90
                }
            },
            { 'name': 'mapDisplayMode',
              'description': 'Display Mode',
              'metadata': {
                    'type': "dropdown",
                    'values': ["region", "markers", "text"],
                    'default': "region"
                }
            },
            { 'name': 'mapRegion',
              'description': 'Region',
              'metadata': {
                    'type': "dropdown",
                    'values': ["world", "US"],
                    'default': "world"
              }
            }
        ]
  