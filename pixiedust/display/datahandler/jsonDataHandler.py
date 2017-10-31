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

import pandas
from pixiedust.utils import Logger
from .pandasDataFrameHandler import PandasDataFrameDataHandler

@Logger()
class JSONDataHandler(PandasDataFrameDataHandler):
    def __init__(self, options, entity):
        self.debug("Creating a Pandas dataframe from JSON entity")
        if not isinstance(entity, list):
            entity = [entity]
        entity = pandas.DataFrame(entity)
        super(JSONDataHandler, self).__init__(options, entity)
