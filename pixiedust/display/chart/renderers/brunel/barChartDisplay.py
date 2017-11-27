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
    def compute_brunel_magic(self):
        parts = ["bar"]
        if self.options.get("orientation", "vertical") == "horizontal":
            parts = ["transpose"] + parts

        parts.append("x({})".format(",".join(self.getKeyFields())))
        parts.append("y({})".format(",".join(self.getValueFields())))
        parts.append(self.get_sort())
        parts.append("color({})".format(self.getKeyFields()[0]))
        #parts.append("filter({})".format(",".join(self.getKeyFields())))

        return " ".join(parts)
