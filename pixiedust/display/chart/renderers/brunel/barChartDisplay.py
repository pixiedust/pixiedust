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
from pixiedust.utils import Logger
from .brunelBaseDisplay import BrunelBaseDisplay

@PixiedustRenderer(id="barChart")
@Logger()
class BarChartRenderer(BrunelBaseDisplay):
    def isSubplot(self):
        return self.options.get("charttype", "grouped") == "subplots"

    def getExtraFields(self):
        if not self.isSubplot() and len(self.getValueFields()) > 1:
            #no clusterby if we are grouped and multiValueFields
            return []

        clusterby = self.options.get("clusterby")
        return [clusterby] if clusterby is not None else []

    def compute_brunel_magic(self):
        parts = ["bar"]
        if self.options.get("orientation", "vertical") == "horizontal":
            parts.append("transpose")

        clusterby = list(filter(None, [self.options.get("clusterby", "")]))

        if self.options.get("charttype", "grouped") == "stacked":
            parts.append("stack")
            parts.append("x({})".format(",".join(self.getKeyFields())))
        else:
            parts.append("x({})".format(",".join(self.getKeyFields() + self.getValueFields())))
        parts.append("y({})".format(",".join(self.getValueFields())))
        parts.append(self.get_sort())
        parts.append("color({})".format(clusterby[0] if len(clusterby) > 0 else self.getKeyFields()[0]))
        return parts
