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
import warnings
from pixiedust.display.app import *
from six import iteritems
from IPython.core.magic import (Magics, magics_class, cell_magic)
from IPython.core.getipython import get_ipython

@magics_class
class PixiedustDebuggerMagics(Magics):
    def __init__(self, shell):
        super(PixiedustDebuggerMagics,self).__init__(shell=shell)

    @cell_magic
    def pixie_debugger(self, line, cell):
        PixieDebugger().run(cell)

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        get_ipython().register_magics(PixiedustDebuggerMagics)
except NameError:
    #IPython not available we must be in a spark executor
    pass

@PixieApp
class PixieDebugger():
    @route()
    def main_screen(self):
        return self.env.getTemplate("mainScreen.html")

    @route(done="*")
    def done_screen(self):
        return "<div>Thank you for using PixieDust Debugger</div>"
