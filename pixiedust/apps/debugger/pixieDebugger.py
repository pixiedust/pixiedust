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
import inspect
import sys
import argparse
from pixiedust.display.app import *
from pixiedust.utils import Logger
from pixiedust.utils.astParse import get_matches_lineno
from six import iteritems, PY3
from IPython.core.magic import (Magics, magics_class, line_cell_magic)
from IPython.core.getipython import get_ipython

@magics_class
class PixiedustDebuggerMagics(Magics):
    def __init__(self, shell):
        super(PixiedustDebuggerMagics,self).__init__(shell=shell)

    @line_cell_magic
    def pixie_debugger(self, line, cell=None):
        args = None
        if line is not None:
            parser = argparse.ArgumentParser(description='PixieDebugger options')
            parser.add_argument('-b', '--breakpoints', nargs='*', help='set breakpoints')
            args = parser.parse_args(line.split())
        PixieDebugger().run({
            "breakpoints": args.breakpoints if args is not None else [],
            "code": cell
        })

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        get_ipython().register_magics(PixiedustDebuggerMagics)
except NameError:
    #IPython not available we must be in a spark executor
    pass

class NoTraceback(Exception):
    "Marker exception for signaling that no traceback was found"
    pass

@PixieApp
@Logger()
class PixieDebugger():
    def initialize(self):
        self.is_post_mortem = False
        self.code =  ""
        self.breakpoints = []
        self.is_post_mortem = self.pixieapp_entity is None or self.pixieapp_entity["code"] is None
        if self.is_post_mortem:
            if not hasattr(sys, "last_traceback") or sys.last_traceback is None:
                raise NoTraceback()
            if self.options.get("debug_route", "false" ) == "true":
                stack = [tb.function if PY3 else tb[3] for tb in inspect.getinnerframes(sys.last_traceback)]
                method_name = stack[-1]
                for method in reversed(stack):
                    code = self.parent_pixieapp.exceptions.get(method, None)
                    if code:
                        method_name = method
                        break
                self.pixieapp_entity = {
                    "breakpoints": ["{}.{}".format(self.parent_pixieapp.__pixieapp_class_name__, method_name)],
                    "code": code or ""
                }
                self.debug("Invoking PixieDebugger for route with {}".format(self.pixieapp_entity))
                self.is_post_mortem = False

        if not self.is_post_mortem:
            self.code = self.renderTemplateString("""
def pixie_run():
    import pdb
    pdb.set_trace()
{{this.pixieapp_entity["code"]|indent(4, indentfirst=True)}}
pixie_run()
        """.strip())
            bps_lines = set()
            bps_fns = set()
            for breakpoint in self.pixieapp_entity["breakpoints"] or []:
                try:
                    bps_lines.add( int(breakpoint))
                except ValueError:
                    matches = get_matches_lineno(self.code, breakpoint)
                    if len(matches) == 0:
                        bps_fns.add(breakpoint)
                    else:
                        for match in matches:
                            bps_lines.add(match)
            self.breakpoints = list(sorted(bps_lines)) + list(sorted(bps_fns))
        else:
            self.code="""
import pdb
pdb.pm()
            """

    @property
    def pm_prefix(self):
        return "$$" if self.is_post_mortem else ""

    @route()
    def main_screen(self):
        try:
            self.initialize()
        except NoTraceback:
            return "<div>Nothing to debug because no Traceback has been produced</div>"
        return self.env.getTemplate("mainScreen.html")

    @route(done="*")
    def done_screen(self):
        return "<div>Thank you for using PixieDust Debugger</div>"
