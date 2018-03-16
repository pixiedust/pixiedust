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

from abc import ABCMeta
from six import with_metaclass
from pixiedust.display.chart.renderers import PixiedustRenderer
from pixiedust.display.chart.renderers.baseChartDisplay import BaseChartDisplay, commonChartOptions

@PixiedustRenderer(rendererId="table")
class TableBaseDisplay(with_metaclass(ABCMeta, BaseChartDisplay)):
    
    def get_options_dialog_pixieapp(self):
            """
            Return the fully qualified path to a PixieApp used to display the dialog options
            PixieApp must inherit from pixiedust.display.chart.options.baseOptions.BaseOptions
            """
            return "pixiedust.display.chart.renderers.table.tableOptions.TableOptions"

    ## overrides empty method in baseChartDisplay
    def getExtraFields(self):
        fieldNames = self.getFieldNames()
        if len(fieldNames) == 0:
            return []
        tableFields = []
        tableFieldStr = self.options.get("tableFields")
        if tableFieldStr is None:
            return fieldNames
        else:
            tableFields = tableFieldStr.split(",")
            tableFields = [val for val in tableFields if val in fieldNames]
        return tableFields

    def canRenderChart(self):
        return (True, None)

    def isTableRenderer(self):
        return True
    
    def supportsKeyFields(self, handlerId):
        return False

    def supportsKeyFieldLabels(self, handlerId):
        return False

    def supportsLegend(self, handlerId):
        return False

    def supportsAggregation(self, handlerId):
        return False

    @commonChartOptions
    def getChartOptions(self):
        return [
            {
                'name': 'table_noschema',
                'description': 'Hide Schema',
                'metadata': {
                    'type': 'checkbox',
                    'default': "false"
                }
            },
            {
                'name': 'table_nosearch',
                'description': 'Hide Search',
                'metadata': {
                    'type': 'checkbox',
                    'default': "false"
                }
            },
            {
                'name': 'table_nocount',
                'description': 'Hide Row Count',
                'metadata': {
                    'type': 'checkbox',
                    'default': "false"
                }
            },
            {
                'name': 'table_showrows',
                'description': 'Show Rows',
                'tooltip': 'Warning: this filter only applies to the sampled data and not the original data set',
                'metadata': {
                    'type': 'dropdown',
                    'values': ['All', 'Missing values', 'Not missing values'],
                    'default': "All"
                }
            }
        ]
    
