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

from abc import abstractmethod, ABCMeta
from pixiedust.display.chart.renderers import PixiedustRenderer
from pixiedust.utils import Logger
from pixiedust.utils.shellAccess import ShellAccess
from six import with_metaclass
from IPython.display import display as ipythonDisplay
from IPython.utils.io import capture_output
from IPython.core.getipython import get_ipython
from ..baseChartDisplay import BaseChartDisplay

@PixiedustRenderer(rendererId="brunel")
@Logger()
class BrunelBaseDisplay(with_metaclass(ABCMeta, BaseChartDisplay)):
    def convert_html(self, output):
        if "text/html" in output.data:
            return output._repr_html_()
        elif "application/javascript" in output.data:
            return """<script type="text/javascript">{}</script>""".format(output._repr_javascript_())
        self.debug("Unused output: {}".format(output.data.keys()))
        return ""

    @abstractmethod
    def compute_brunel_magic(self):
        pass

    def complete_magic(self, magic):
        return magic + ":: width={}, height={}".format(
            int(self.getPreferredOutputWidth()), int(self.getPreferredOutputHeight())
        )

    def get_sort(self):
        sortby = self.options.get("sortby", None)
        if sortby == 'Keys ASC':
            return "sort({})".format(",".join([key+":ascending" for key in self.getKeyFields()]))
        elif sortby == 'Keys DESC':
            return "sort({})".format(",".join([key+":descending" for key in self.getKeyFields()]))
        elif sortby == 'Values ASC':
            return "sort({})".format(",".join([key+":ascending" for key in self.getValueFields()]))
        elif sortby == 'Values DESC':
            return "sort({})".format(",".join([key+":descending" for key in self.getValueFields()]))
        return ""

    def doRenderChart(self):
        payload = self.compute_brunel_magic()
        if not isinstance(payload, tuple):
            payload = (self.getWorkingPandasDataFrame(), payload)
        pandas_df, magic = payload
        ShellAccess['brunel_temp_df'] = pandas_df
        try:
            with capture_output() as buf:
                magic = "data('brunel_temp_df') {}".format(self.complete_magic(magic))
                self.debug("Running brunel with magic {}".format(magic))
                data = get_ipython().run_line_magic('brunel', magic)
                if data is not None:
                    ipythonDisplay(data)
            brunel_html = "\n".join([self.convert_html(output) for output in buf.outputs])
            return brunel_html
        finally:
            del ShellAccess['brunel_temp_df']

