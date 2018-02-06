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
from .baseOptions import BaseOptions
import re

@Logger()
class ChartOptionTitle(object):
    @route(widget="pdChartOptionTitle")
    def chart_option_title_widget(self, optid, title):
        return """
<label for="chartoption{{optid}}{{prefix}}">Chart Title:</label>
<input type="text" class="form-control" id="chartoption{{optid}}{{prefix}}" name="{{optid}}" value="{{title or ""}}"
    pd_script="self.options_callback('title', '$val(chartoption{{optid}}{{prefix}})')" onkeyup="$(this).trigger('click');">
"""

@PixieApp
@Logger()
class OptionsShell(BaseOptions, ChartOptionTitle):
    def camel_case_to_title(self, name):
        return re.compile('([a-z0-9])([A-Z])').sub(r'\1 \2', name).title()

    def get_custom_options(self):
        "Options for this dialog"
        t = self.camel_case_to_title(self.parsed_command['kwargs']['handlerId']) if 'kwargs' in self.parsed_command and 'handlerId' in self.parsed_command['kwargs'] else 'Chart'
        return {
            "runInDialog":"true",
            "title": t + " Options",
            "showFooter":"true",
            "customClass":"pixiedust-default-dialog"
        }

    def setup(self):
        BaseOptions.setup(self)
        self.chart_options = [{
            "optid": "title",
            "title": lambda: self.run_options.get("title") or "",
            "widget": "pdChartOptionTitle"
        }]
        self.new_options = {}

    def options_callback(self, option, value):
        # self.options[option] = value
        self.new_options[option] = value

    def get_option(self, optid=None, widget=None):
        """
        returns the first chart_option that matches the given arguments
        """
        index = self.get_option_index(optid=optid, widget=widget)
        return None if index == -1 else self.chart_options[index]

    def get_option_index(self, optid=None, widget=None):
        """
        returns the index of the first chart_option that matches the given arguments
        """
        if self.chart_options is None or len(self.chart_options) == 0:
            return -1
        elif optid is None and widget is None:
            return -1
        else:
            option = -1
            for index, chartopt in enumerate(self.chart_options):
                if (optid is None or chartopt['optid'] == optid) and (widget is None or chartopt['widget'] == widget):
                    option = index
                if option != -1:
                    break
            return option

    @route()
    def main_screen(self):
        self.fieldNamesAndTypes = self.get_field_names_and_types(True, True)
        self.fieldNames = self.get_field_names(True)
        self._addHTMLTemplate("optionsshell.html")

    def get_new_options(self):
        return self.new_options
