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

from pixiedust.display.app import route
from pixiedust.utils import Logger
import six

@Logger()
class KeyValueSelector(object):
    @route(widget="pdKeyValueSelector")
    def chart_option_key_value_widget(self, optid, keyFields, valueFields):
        self.keyFields = keyFields.split(",") if isinstance(keyFields, six.string_types) else keyFields or []
        self.valueFields = valueFields.split(",") if isinstance(valueFields, six.string_types) and valueFields else valueFields or []
        self.keyFieldsSupported = self.key_fields_supported()
        self.keyFieldsType = self.key_fields_type()
        self.valueFieldsType = self.value_fields_type()
        self._addHTMLTemplate("keyvalueselector.html")

    def key_fields_supported(self):
        return self.get_renderer.supportsKeyFields(self.parsed_command['kwargs']['handlerId'])

    def key_fields_type(self):
        return ['string', 'numeric', 'date/time']

    def value_fields_type(self):
        return ['numeric']
