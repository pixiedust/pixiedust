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
from pixiedust.display.chart.options.optionsShell import *
from pixiedust.display.chart.options.components.TableValueSelector import *
from pixiedust.display.chart.options.components.AggregationSelector import *
from pixiedust.display.chart.options.components.RowCount import *

@PixieApp
@Logger()
class TableOptions(OptionsShell, TableValueSelector, AggregationSelector, RowCount):
    def setup(self):
        OptionsShell.setup(self)
        # self.chart_options.append({
        #     "optid": "keyvalue",
        #     "classname": "no_loading_msg",
        #     "keyFields": None,
        #     "valueFields": lambda: self.options.get("valueFields") or "",
        #     "widget": "pdTableValueSelector"
        # })

        self.chart_options.append({
            "optid": "rowCount",
            "classname": "field-width-50 no_loading_msg",
            "count": lambda: self.options.get("rowCount") or 500,
            "widget": "pdRowCount"
        })

    def value_fields_type(self):
        return ['any']

    def aggregation_supported(self):
        return self.get_renderer.supportsAggregation(self.parsed_command['kwargs']['handlerId'])
