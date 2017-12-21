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
from pixiedust.display.app import *
from .baseOptions import BaseOptions
from pixiedust.display import display
from pixiedust.utils.shellAccess import ShellAccess
from IPython.core.getipython import get_ipython
from pixiedust.utils import Logger

@PixieApp
@Logger()
class TestOptions(BaseOptions):
    @route()
    def main_screen(self):
        return """
<div class="field-container row">
    <div class="col-sm-6" style="padding: 0px 5px 0px 0px;">
        <ul>
            {%for field in this.data_handler.getFieldNames(True)%}
            <li>
                {{field}}
            </li>
            {%endfor%}
        </ul>
    </div>
</div>
    """

    def get_new_options(self):
        return {}