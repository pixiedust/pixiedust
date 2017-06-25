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

class StreamingDataAdapter(with_metaclass(ABCMeta)):
    @abstractmethod
    def getNextData(self):
        """Return the next batch of data from the underlying stream. 
        Accepted return values are:
        1. (x,y): tuple of list/numpy arrays representing the x and y axis
        2. pandas dataframe
        3. y: list/numpy array representing the y axis. In this case, the x axis is automatically created
        4. pandas serie: similar to #3
        """
        pass