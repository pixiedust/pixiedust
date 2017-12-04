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

@PixiedustRenderer(id="pieChart")
@Logger()
class PieChartRenderer(BrunelBaseDisplay):
    def compute_brunel_magic(self):
        parts = ["stack polar bar"]

        for index, key in enumerate(self.getKeyFields()):
            if index > 0:
                parts.append("+ line")
            parts.append("""x("const")""")
            parts.append("y(#count)")
            parts.append("color({0})".format(key))
            parts.append("legends(none)")
            parts.append("label({})".format(key))

        return parts
