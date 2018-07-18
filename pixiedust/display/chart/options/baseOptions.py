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
from abc import abstractmethod, ABCMeta
from six import iteritems
from pixiedust.display.app import *
from pixiedust.utils.astParse import parse_function_call
from pixiedust.utils import cache, Logger
from pixiedust.display.datahandler import getDataHandler
from pixiedust.display.chart.renderers import PixiedustRenderer
from pixiedust.utils.shellAccess import ShellAccess
from IPython.core.getipython import get_ipython

@PixieApp
@Logger()
class BaseOptions(with_metaclass(ABCMeta)):
    def setup(self):
        self.parsed_command = parse_function_call(self.parent_command) #pylint: disable=E1101,W0201
        self.parent_entity = self.parsed_command['args'][0] if len(self.parsed_command['args'])>0 else None
        if self.parent_entity is not None:
            try:
                self.parent_entity = eval(self.parent_entity, get_ipython().user_ns) #pylint: disable=W0123
            except Exception as exc:
                self.exception(exc)
                self.entity = None

        #apply the cell_metadata
        if getattr(self, "cell_metadata"):
            self.parsed_command['kwargs'].update( 
                self.cell_metadata.get("pixiedust",{}).get("displayParams",{})
            )

    @cache(fieldName="fieldNames")
    def get_field_names(self, expandNested=True):
        return self.data_handler.getFieldNames(expandNested)

    @cache(fieldName="fieldNamesAndTypes")
    def get_field_names_and_types(self, expandNested=True, sorted=False):
        return self.data_handler.getFieldNamesAndTypes(expandNested, sorted)

    def get_custom_options(self):
        "Options for this base dialog"
        return {
            "runInDialog":"true",
            "title":"Test",
            "showFooter":"true"
        }

    def on_ok(self, **kwargs):
        run_options = self.run_options
        #update with the new options
        run_options.update(self.get_new_options())
        command = "{}({},{})".format(
            self.parsed_command['func'],
            self.parsed_command['args'][0],
            ",".join(
                ["{}='{}'".format(k, v) for k, v in iteritems(run_options)]
            )
        )
        js = self.env.from_string("""
            pixiedust.executeDisplay(
                {{this.get_pd_controls(
                    command=command, 
                    avoidMetadata=avoid_metadata, 
                    override_keys=override_keys,
                    options=run_options, 
                    black_list=['nostore_figureOnly'],
                    prefix=this.run_options['prefix'],
                ) | tojson}}
            );
        """).render(
            this=self, 
            run_options=run_options, 
            command=command, 
            avoid_metadata=kwargs.get("avoid_metadata", True),
            override_keys=kwargs.get("override_keys", [])
        )
        return self._addJavascript(js)

    @property
    def run_options(self):
        black_list = ['runInDialog','nostore_figureOnly','targetDivId','nostore_cw']
        return {key:value for key,value in iteritems(self.parsed_command['kwargs']) if key not in black_list}

    @property
    def data_handler(self):
        return getDataHandler(
            self.parsed_command['kwargs'], self.parent_entity
        ) if self.parent_entity is not None else None

    @property
    def get_renderer(self):
        return PixiedustRenderer.getRenderer(
            self.parsed_command['kwargs'],
            self.parent_entity, False
        ) if self.parent_entity is not None else None

    @abstractmethod
    def get_new_options(self):
        "return a dictionary of the new options selected by the user"
        pass
