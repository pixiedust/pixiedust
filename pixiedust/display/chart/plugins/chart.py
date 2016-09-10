# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2016
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
from mpld3 import plugins

class ChartPlugin(plugins.PluginBase):  # inherit from PluginBase
    """Chart plugin to fix xticks that are overriden by mpld3 while converting from matplotlib """

    def __init__(self, display, xtick_labels):
        ChartPlugin.JAVASCRIPT = display.renderTemplate("chartPlugin.js")
        self.dict_ = {"type": "chart","labels": xtick_labels}