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
class RowCount(object):
    @route(widget="pdRowCount")
    def chart_option_rowcount_widget(self, optid, count):
        self.rowCount = count or 100
        return """
<script>
    var rowCountStatus{{optid}}{{prefix}} = true
    function rowCount{{optid}}{{prefix}}(input) {
        var val = $(input).val()
        var invalid = !val || isNaN(val) || Math.floor(Number(val)) < 1
        if (rowCountStatus{{optid}}{{prefix}} && invalid) {
            rowCountStatus{{optid}}{{prefix}} = false
            chartOptionsOKStatus{{prefix}}(true)
        } else if (!rowCountStatus{{optid}}{{prefix}} && !invalid) {
            chartOptionsOKStatus{{prefix}}(false)
            rowCountStatus{{optid}}{{prefix}} = true
            $(input).trigger('click')
        }
    }
</script>
<div class="form-group">
    <label class="field"># of Rows to Display:</label>
    <input id="chartoption{{optid}}{{prefix}}" class="form-control" name="{{optid}}" type="number" min="1" max="10000" value="{{this.rowCount}}"
          pd_script="self.options_callback('{{optid}}','$val(chartoption{{optid}}{{prefix}})')" onkeyup="rowCount{{optid}}{{prefix}}(this)">
</div>
"""
