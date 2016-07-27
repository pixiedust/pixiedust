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

from .mpld3ChartDisplay import Mpld3ChartDisplay
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np

class PieChart2Display(Mpld3ChartDisplay):

	def setChartLegend(self, handlerId, fig, ax):
		pass

	def setChartGrid(self, handlerId, fig, ax):
		pass
	
	def doRenderMpld3(self, handlerId, fig, ax, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues):
		numPieCharts = len(valueFields)
		colors = cm.jet(np.linspace(0., 1., len(keyFieldValues)))
		if numPieCharts > 1:
			fig.delaxes(ax)
			if numPieCharts < 3:
				pieChartGridPrefix = "1" + str(numPieCharts)
			elif numPieCharts <= 4:
				pieChartGridPrefix = "22"
			else:
				pieChartGridPrefix = str(int(math.ceil(numPieCharts//3))) + "3"
			for i, valueField in enumerate(valueFields):
				ax2 = fig.add_subplot(pieChartGridPrefix + str(i+1))
				ax2.pie(valueFieldValues[i], labels=keyFieldLabels, colors=colors, explode=None, autopct='%1.1f%%')
				ax2.set_title(valueFields[i], fontsize=18);
				ax2.axis("equal")
		else:
			ax.pie(valueFieldValues[0], labels=keyFieldLabels, colors=colors, explode=None, autopct='%1.1f%%')
			ax.set_title(valueFields[0], fontsize=18);
			ax.axis("equal")
