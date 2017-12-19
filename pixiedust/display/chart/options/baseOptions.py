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
from six import iteritems
from pixiedust.display.app import *
from pixiedust.utils.astParse import parse_function_call
from pixiedust.utils import Logger
from IPython.core.getipython import get_ipython
from pixiedust.display.datahandler import getDataHandler
from pixiedust.utils.shellAccess import ShellAccess

@PixieApp
@Logger()
class BaseOptions():
    def setup(self):
        self.parsed_command = parse_function_call(self.parent_command) #pylint: disable=E1101,W0201
        self.parent_entity = self.parsed_command['args'][0] if len(self.parsed_command['args'])>0 else None
        if self.parent_entity is not None:
            try:
                self.parent_entity = eval(self.parent_entity, get_ipython().user_ns) #pylint: disable=W0123
            except Exception as exc:
                self.exception(exc)
                self.entity = None

    def on_ok(self):
        try:
            #reconstruct the parent command with the new options
            for key in ShellAccess:
                locals()[key] = ShellAccess[key]
            entity = eval(self.parsed_command['args'][0], globals(), locals())
            run_options = self.run_options
            command = "{}({},{})".format(
                self.parsed_command['func'],
                self.parsed_command['args'][0],
                ",".join(
                    ["{}='{}'".format(k, v) for k, v in iteritems(run_options)]
                )
            )
            sys.modules['pixiedust.display'].pixiedust_display_callerText = command
            display(entity, **run_options)
        finally:
            del sys.modules['pixiedust.display'].pixiedust_display_callerText

    @property
    def run_options(self):
        black_list = ['runInDialog','nostore_figureOnly','targetDivId','nostore_cw']
        return {key:value for key,value in iteritems(self.parsed_command['kwargs']) if key not in black_list}

    @property
    def data_handler(self):
        return getDataHandler(
            self.parsed_command['kwargs'], self.parent_entity
        ) if self.parent_entity is not None else None
