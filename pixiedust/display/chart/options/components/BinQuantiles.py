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
class BinQuantiles(object):
    @route(widget="pdBinQuantiles")
    def chart_option_binranges_widget(self, optid, numbins, quantiles):
        htmlArr = []
        htmlArr.append("""
<script type="text/javascript">
// need to return list back as a string in the form "0.0,0.25,0.50,0.75,1.0"
function getQuantilesStr() {
    var quantiles = [];
    $('.quantile-val').each(function() {
        quantiles.push($(this).val());
    });
    return quantiles.join(',');
}
// check if sorted and all in between 0.0 and 1.0
function validateQuantiles(quantilesStr) {
    var quantiles = quantilesStr.split(',').map(parseFloat);
    var isValid = true;
    var prev = quantiles[0];
    isValid = prev >= 0.0 && prev <= 1.0;
    for (var i = 1; i < quantiles.length; i++) {
        var curr = quantiles[i];
        if (prev < curr && curr >= 0.0 && curr <= 1.0) {
            prev = curr;
        } else {
            console.log('some data is invalid');
            isValid = false;
            break;
        }
    }
    return isValid;
}
function updateQuantiles() {
    var quantilesStr = getQuantilesStr();
    chartOptionsOKStatus{{prefix}}(!validateQuantiles(quantilesStr));
    return quantilesStr;
}
updateQuantiles();
</script>
<p>Edit bin quantiles.  Values should be between [0.0, 1.0].  Bins should be in ascending order.</p><br/>
        """)
        quantileVals = quantiles.split(",")
        if len(quantileVals) != int(numbins):
            quantileVals = self.generateQuantiles(int(numbins)).split(",")
        for i in range(int(numbins)):
            htmlArr.append("""
<div class="form-group">
    <label for="quantile_{0}_{{{{optid}}}}{{{{prefix}}}}">Quantile {0} Percentage:</label>
    <input id="quantile_{0}_{{{{optid}}}}{{{{prefix}}}}" class="quantile-val form-control" name="quantile_{0}" type="number" min="0.0" max="1.0" step="0.01" value="{1}"
        pd_script="self.options_callback('quantiles','$val(updateQuantiles)')" onkeyup="updateQuantiles()">
</div>
        """.format(i+1, quantileVals[i]))
        return "".join(htmlArr)
