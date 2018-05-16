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

@PixieApp
class TemplateTabbedApp():
    """Templated PixieApp that provide tab layout"""
    def setup(self):
        self.apps = []

    @route()
    def main_screen(self):
        if len(self.apps) == 0:
            return """
<h1>No app defined </h1>
<div>Try to define the apps in a setup method e.g.
<code>
def setup(self):
    self.apps=[{"title":"My app", "app_class": "my.package.MyApp"}]
</code>
"""
        
        return """
<ul class="nav nav-tabs" role="tablist">
{%for app in this.apps%}
    <li role="presentation" id="tab_{{prefix}}_{{loop.index}}" {%if loop.first%}class="active"{%endif%}>
        <a href="#content_{{prefix}}_{{loop.index}}" data-toggle="tab">{{app['title']}}</a>
    </li>
{%endfor%}
</ul>
<div class="tab-content">
{%for app in this.apps%}
    <div role="tabpanel" class="tab-pane {%if loop.first%}active{%endif%} no_loading_msg" 
        id="content_{{prefix}}_{{loop.index}}">
        <div pd_render_onload pd_app="{{app['app_class']}}"></div>
    </div>
{%endfor%}
</div>
<script>
$('#tab_{{prefix}}_1').click();
</script>        
"""