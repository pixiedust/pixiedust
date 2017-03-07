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
import math

def append(displayObject, arr, option):
    if displayObject.acceptOption(option["name"]):
        arr.append(option)

def clusterBy(displayObject):
    return { 
        'name': 'clusterby',
        'description': 'Cluster By',
        'refresh': True,
        'metadata': {
            'type': "dropdown",
            'values': ["None"] + sorted([f for f in displayObject.getFieldNames() if f not in displayObject.getKeyFields() and f not in displayObject.getValueFields()]),
            'default': ""
        },
        'validate': lambda option:\
            (option in displayObject.getFieldNames() and option not in displayObject.getKeyFields() and option not in displayObject.getValueFields(),\
             "Cluster By value is already used in keys or values for this chart")
    }

def barChart(displayObject):
    options = []
    options.append(clusterBy(displayObject))

    if not hasattr(displayObject, 'no_orientation') or displayObject.no_orientation is not True:
        options.append({
            'name': 'orientation',
            'description': 'Orientation',
            'metadata': {
                'type': 'dropdown',
                'values': ['vertical', 'horizontal'],
                'default': "vertical"
            }
        })

    if displayObject.options.get("clusterby") != None or len(displayObject.getValueFields()) > 1:
        options.append({
            'name': 'charttype',
            'description': 'Type',
            'metadata': {
                'type': 'dropdown',
                'values': ['grouped', 'stacked', 'subplots'],
                'default': "grouped"
            }
        })

    options.append({
        'name': 'legend',
        'description': 'Show legend',
        'metadata': {
            'type': 'checkbox',
            'default': "true"
        }
    })

    return options

def lineChart(displayObject):
    options = []

    options.append(clusterBy(displayObject))

    if displayObject.options.get("clusterby") != None or len(displayObject.getValueFields()) > 1:
        options.append({
            'name': 'lineChartType',
            'description': 'Type',
            'metadata': {
                'type': 'dropdown',
                'values': ['grouped', 'subplots'],
                'default': "grouped"
            }
        })

    options.append({
        'name': 'legend',
        'description': 'Show legend',
        'metadata': {
            'type': 'checkbox',
            'default': "false"
        }
    })

    options.append({
        'name': 'logx',
        'description': 'log scale on x',
        'metadata': {
            'type': 'checkbox',
            'default': "false"
        }
    })
    options.append({
        'name': 'logy',
        'description': 'log scale on y',
        'metadata': {
            'type': 'checkbox',
            'default': "false"
        }
    })
    return options

def histogram(displayObject):
    options = []
    if len(displayObject.getValueFields()) > 1:
        append(displayObject, options, {
            'name': 'histoChartType',
            'description': 'Type',
            'metadata': {
                'type': 'dropdown',
                'values': ['stacked', 'subplots'],
                'default': "stacked"
            }
        })
    count = len(displayObject.getWorkingPandasDataFrame().index)
    options.append({
        'name': 'binsize',
        'description': 'Bin size',
        'metadata': {
            'type': 'slider',
            'max': int(max(math.ceil(count / 2), 4)),
            'min': int(max(math.floor(count / 20), 2)),
            'default': int(max(math.ceil(count / 4), 3))
        }
    })
    return options

commonOptions = {}
for f in [barChart,lineChart,histogram]:
    commonOptions.update({f.__name__:f})
