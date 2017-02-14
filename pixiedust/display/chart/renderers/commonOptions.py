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

def barChart(displayObject):
    options = [
        {
            'name': 'orientation',
            'description': 'Orientation',
            'metadata': {
                'type': 'dropdown',
                'values': ['vertical', 'horizontal'],
                'default': "vertical"
            }
        }
    ]
    if len(displayObject.getKeyFields()) > 1 or len(displayObject.getValueFields()) > 1:
        options.insert(0,
            {
                'name': 'charttype',
                'description': 'Type',
                'metadata': {
                    'type': 'dropdown',
                    'values': ['grouped', 'stacked', 'subplots'],
                    'default': "grouped"
                }
            }
        )

    return options

funcs=[barChart]

commonOptions = {}
for f in funcs:
    commonOptions.update({f.__name__:f})
