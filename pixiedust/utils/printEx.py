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

__all__=['printEx','PrintColors']

class PrintColors(object):
    PURPLE = '\x1b[35m'
    CYAN = '\x1b[36m'
    DARKCYAN = '\x1b[36m'
    BLUE = '\x1b[34m'
    GREEN = '\x1b[32m'
    YELLOW = '\x1b[33m'
    RED = '\x1b[31m'
    BOLD = '\x1b[1m'
    UNDERLINE = '\x1b[4m'
    BLINK = '\x1b[5m'
    END = '\x1b[0m'
    
def printEx(message, color=None):
    if not color:
        print(message)
    else:
        print( color + message + PrintColors.END)
