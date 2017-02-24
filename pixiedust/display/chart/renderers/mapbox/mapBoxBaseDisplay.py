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

from pixiedust.display.chart.renderers import PixiedustRenderer
from ..baseChartDisplay import BaseChartDisplay
from six import with_metaclass
from abc import ABCMeta

import pixiedust

myLogger = pixiedust.getLogger(__name__)

@PixiedustRenderer(rendererId="mapbox")
class MapBoxBaseDisplay(with_metaclass(ABCMeta, BaseChartDisplay)):
	pass

	def getChartOptions(self):
		return [
			{ 'name': 'kind',
			  'metadata': {
					'type': "dropdown",
					'values': ["simple","choropleth","densitymap"],
					'default': "simple"
				}
			}
		]

    