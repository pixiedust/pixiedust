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
from pixiedust.display.chart.renderers.baseChartDisplay import commonChartOptions
from .seabornBaseDisplay import SeabornBaseDisplay
import pandas as pd
import numpy as np
import seaborn as sns

@PixiedustRenderer(id="scatterPlot")
class ScatterPlotDisplay(SeabornBaseDisplay):
	def supportsAggregation(self, handlerId):
		return False
    
	def canRenderChart(self):
		valueFields = self.getValueFields()
		if len(valueFields) != 1:
			return (False, "Can only specify one Value Field")

		#Verify that all key field are numericals
		for keyField in self.getKeyFields():
			if not self.dataHandler.isNumericField(keyField):
				return (False, "Column {0} is not numerical".format(keyField))
		
		return (True, None)

	def getPreferredDefaultValueFieldCount(self, handlerId):
		return 2

	def createFigure(self):
		valueFields = self.getValueFields()
		keyFields = self.getKeyFields()
		facetGrid = sns.jointplot(x=keyFields[0], y=valueFields[0], kind=self.options.get("kind","scatter"), data=self.getWorkingPandasDataFrame())
		return facetGrid.fig, facetGrid.fig.axes[0]

	def matplotlibRender(self, fig, ax):
		pass

	@commonChartOptions
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