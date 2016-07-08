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

from .display import ChartDisplay
from pylab import *
import mpld3
from pyspark.sql import functions as F
    
class PieChartDisplay(ChartDisplay):
    def doRender(self, handlerId):
        displayColName = self.getFirstNumericalColInfo()
        if not displayColName:
            self._addHTML("Unable to find a numerical column in the dataframe")
            return

        mpld3.enable_notebook() 
        # make a square figure and axes
        figure(1, figsize=(6,6))
        ax = axes([0.1, 0.1, 0.8, 0.8])

        # The slices will be ordered and plotted counter-clockwise.
        #labels = 'Frogs', 'Hogs', 'Dogs', 'Logs'
        #fracs = [15, 30, 45, 10]
        explode=(0, 0, 0.1, 0)

        pand = self.entity.groupBy(displayColName).agg(F.count(displayColName).alias("count")).toPandas()
        x = pand["count"].dropna().tolist()
        labels=pand[displayColName].tolist()

        pie(x, labels=labels, explode=explode, autopct='%1.1f%%', startangle=90)
                        # The default startangle is 0, which would start
                        # the Frogs slice on the x-axis.  With startangle=90,
                        # everything is rotated counter-clockwise by 90 degrees,
                        # so the plotting starts on the positive y-axis.

        title(displayColName.lower() + ' totals', bbox={'facecolor':'0.8', 'pad':5})

        show()