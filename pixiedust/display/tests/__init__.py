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

from ..display import *
from .test1 import *
from .test2 import *

#Make sure that matplotlib is running inline
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    #get_ipython().run_line_magic("matplotlib", "inline")

class TestsDisplayMeta(DisplayHandlerMeta):
    @addId
    def getMenuInfo(self,entity):
        if safeCompare(entity, "test1"):
            return [
                {"categoryId": "Test", "title": "Test1", "icon": "fa-bar-chart", "id": "Test1"}
            ]
        elif safeCompare(entity, "test2"):
            return [
                {"categoryId": "Test", "title": "Test2", "icon": "fa-bar-chart", "id": "Test2"}
            ]
        else:
            return []
    def newDisplayHandler(self,options,entity):
        handlerId=options.get("handlerId")
        if handlerId == "Test1":
            return Test1Display(options,entity)
        else:
            return Test2Display(options,entity)

registerDisplayHandler(TestsDisplayMeta())