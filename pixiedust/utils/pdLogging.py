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

import logging
from logging.handlers import MemoryHandler
from IPython.core.magic import (Magics, magics_class, line_magic)

from collections import deque
logMessageBufferSize = 200
logMessages=deque([], logMessageBufferSize)

class PixiedDustLoggingHandler(logging.Handler):
    def emit(self, record):
        logMessages.append((record.levelno, self.format(record)))

#init pixiedust logging
pixiedustHandler = PixiedDustLoggingHandler()
pixiedustHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
memHandler = MemoryHandler(1, target=pixiedustHandler)
memHandler.setLevel(logging.DEBUG)

pixiedustLogger = logging.getLogger("PixieDust")
pixiedustLogger.addHandler(memHandler)
pixiedustLogger.setLevel(logging.DEBUG)

@magics_class
class PixiedustLoggingMagics(Magics):
    @line_magic
    def pixiedustLog(self, arg_s):
        try:
            opts,args = self.parse_options( arg_s, "l:f:m:")
            level = logging.getLevelName( opts.get("l", "INFO").upper() )
            if not isinstance(level, int):
                level = logging.getLevelName("INFO")
            lookup = opts.get("f", None)
            maxLines = int(opts.get("m", logMessageBufferSize))
            start = len(logMessages) - maxLines - 1
            for i, (l,record) in enumerate(logMessages):
                if i > start and l >= level and (lookup is None or lookup in record): 
                    print(record)
        except:
            print("""Usage Error: -l logLevel -f lookupString -m 20
                -l: filter by log level e.g  'CRITICAL':'FATAL': 'ERROR': 'WARNING':'INFO':'DEBUG'
                -f: filter message that contain given string e.g. "Exception" 
                -m: max number of log messages returned
            """)
            raise

try:
    get_ipython().register_magics(PixiedustLoggingMagics)
except NameError:
    #IPython not available we must be in a spark executor
    pass

def getPixiedustLogger():
    return pixiedustLogger

loggerDict={}
def getLogger(loggerName):
    logger = loggerDict.get(loggerName)
    if logger is None:
        logger = logging.getLogger(loggerName)
        logger.addHandler(memHandler)
        logger.setLevel(logging.DEBUG)
        logger.propagate=0
        loggerDict[loggerName]=logger
    return logger