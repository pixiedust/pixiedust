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
from .optionsShell import OptionsShell
from .components import KeyValueSelector
from .components import AggregationSelector
from .components import RowCount

@PixieApp
@Logger()
class DefaultOptions(OptionsShell, KeyValueSelector, AggregationSelector, RowCount):
    def setup(self):
        OptionsShell.setup(self)
        self.chart_options.append({
            "optid": "keyvalue",
            "classname": "no_loading_msg",
            "keyFields": lambda: self.run_options.get("keyFields") or "",
            "valueFields": lambda: self.options.get("valueFields") or "",
            "widget": "pdKeyValueSelector"
        })

        if self.aggregation_supported():
            self.chart_options.append({
                "optid": "aggregation",
                "classname": "field-width-50 no_loading_msg",
                "aggregation": lambda: self.run_options.get("aggregation") or "",
                "widget": "pdAggregationSelector"
            })

        self.chart_options.append({
            "optid": "rowCount",
            "classname": "field-width-50 no_loading_msg",
            "count": lambda: self.run_options.get("rowCount") or 100,
            "widget": "pdRowCount"
        })

    def aggregation_supported(self):
        return self.get_renderer.supportsAggregation(self.parsed_command['kwargs']['handlerId'])
