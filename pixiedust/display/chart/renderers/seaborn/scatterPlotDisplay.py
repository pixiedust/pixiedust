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
from .seabornBaseDisplay import SeabornBaseDisplay
import pandas as pd
import numpy as np
import seaborn as sns

@PixiedustRenderer(id="scatterPlot")
class ScatterPlotDisplay(SeabornBaseDisplay):
	def supportsAggregation(self, handlerId):
		return False

	def supportsLegend(self, handlerId):
		return False

	def supportsKeyFields(self, handlerId):
		return False
    
	def canRenderChart(self):
		valueFields = self.getValueFields()
		if len(valueFields) < 2:
			return (False, "At least two numerical columns required.")
		else:
			return (True, None)

	def getPreferredDefaultValueFieldCount(self, handlerId):
		return 2

	def createFigure(self):
		valueFields = self.getValueFields()
		facetGrid = sns.jointplot(x=valueFields[0], y=valueFields[1], kind=self.options.get("kind","scatter"), data=self.getPandasDataFrame())
		return facetGrid.fig, facetGrid.fig.axes[0]

	def matplotlibRender(self, fig, ax):
		pass

	def getChartOptions(self):
		return [
			{ 'name': 'kind',
			  'metadata': {
					'type': "dropdown",
					'values': ["scatter", "reg", "resid", "kde", "hex"],
					'default': "scatter"
				}
			}
		]