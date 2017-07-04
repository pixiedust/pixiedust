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
from six import with_metaclass

class StreamingDataAdapter(with_metaclass(ABCMeta)):
    def __init__(self):
        self.channels = []
        
    def getNextData(self):
        nextData = self.doGetNextData()
        if nextData is not None and hasattr(self, "channels"):
            for channel in self.channels:
                channel.processNextData(nextData)
        return nextData

    @abstractmethod
    def doGetNextData(self):
        """Return the next batch of data from the underlying stream. 
        Accepted return values are:
        1. (x,y): tuple of list/numpy arrays representing the x and y axis
        2. pandas dataframe
        3. y: list/numpy array representing the y axis. In this case, the x axis is automatically created
        4. pandas serie: similar to #3
        """
        pass

    def getStreamingChannel(self, processfn, initialData = None):
        channel = StreamingChannel(processfn, initialData)
        if not hasattr(self, "channels"):
            self.channels = []
        self.channels.append(channel)
        return channel
    
class StreamingChannel(StreamingDataAdapter):
    def __init__(self, processfn, initialData):
        super(StreamingChannel,self).__init__()
        self.processfn = processfn
        self.processedData = None
        self.accumulator = initialData

    def processNextData(self, nextData):
        newProcessedData, self.accumulator = self.processfn(self.accumulator, nextData)
        #merge
        self.processedData = newProcessedData if self.processedData is None else self.processedData + newProcessedData
        
    def doGetNextData(self):
        nextData = self.processedData
        self.processedData = None
        return nextData