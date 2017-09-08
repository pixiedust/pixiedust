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
import pandas
from pixiedust.utils.dataFrameAdapter import PandasDataFrameAdapter

__all__ = ['StreamingDataAdapter'] 

class StreamingDataAdapter(with_metaclass(ABCMeta)):
    def __init__(self):
        self.channels = []
        
    def getNextData(self):
        nextData = self.doGetNextData()
        if nextData is not None and hasattr(self, "channels"):
            for channel in self.channels:
                channel.processNextData(nextData)
        return nextData

    def getMetadata(self):
        return {}

    def accept(self, handlerId):
        return True

    defaultValues = {
        "getFieldNames": lambda expandNested=False: [],
        "schema": PandasDataFrameAdapter(pandas.DataFrame()).schema,
        "getWorkingPandasDataFrame": lambda xFields, yFields, extraFields=[], aggregation=None, maxRows = 100: pandas.DataFrame()
    }

    def getDisplayDataHandler(self, options, entity):
        from pixiedust.display.datahandler.baseDataHandler import BaseDataHandler
        this = self
        class StreamingDisplayDataHandler(BaseDataHandler):
            def __init__(self, options, entity):
                super(StreamingDisplayDataHandler, self).__init__(options, entity)
                self.isStreaming = True
            def __getattr__(self, name):
                if hasattr(this, name):
                    return self.this.__getattribute__(name)
                elif name in StreamingDataAdapter.defaultValues:
                    return StreamingDataAdapter.defaultValues[name]
                raise AttributeError("{0} attribute not found".format(name))
            def accept(self, handlerId):
                return this.accept(handlerId)
        return StreamingDisplayDataHandler(options, entity)

    @abstractmethod
    def doGetNextData(self):
        """Return the next batch of data from the underlying stream. 
        Accepted return values are:
        1. (x,y): tuple of list/numpy arrays representing the x and y axis
        2. pandas dataframe
        3. y: list/numpy array representing the y axis. In this case, the x axis is automatically created
        4. pandas serie: similar to #3
        5. json
        6. geojson
        7. url with supported payload (json/geojson)
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