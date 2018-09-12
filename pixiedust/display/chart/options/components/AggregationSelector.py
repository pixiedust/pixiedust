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

from pixiedust.display.app import route
from pixiedust.utils import Logger

@Logger()
class AggregationSelector(object):
    @route(widget="pdAggregationSelector")
    def chart_option_aggregation_widget(self, optid, aggregation):
        self.aggOpts = self.aggregation_options()
        self.aggOpts.sort()
        if not aggregation:
            aggregation = self.aggregation_default()
        self.selectedAgg = aggregation
        return """
<div class="form-group">
    <label class="field">Aggregation:</label>
    <select id="chartoption{{optid}}{{prefix}}" class="form-control" name="{{optid}}" style="margin-left: 0px;"
        onchange="$(this).find('> option:selected').trigger('click')"
        pd_script="self.options_callback('{{optid}}','$val(chartoption{{optid}}{{prefix}})')">
        {% for aggOpt in this.aggOpts %}
        <option value="{{aggOpt}}" {{'selected' if this.selectedAgg == aggOpt}}>{{aggOpt}}</option>
        {% endfor %}
    </select>
</div>
"""

    def aggregation_options(self):
        return ["SUM","AVG","MIN","MAX","COUNT"]

    def aggregation_default(self):
        return self.get_renderer.getDefaultAggregation(self.parsed_command['kwargs']['handlerId'])

