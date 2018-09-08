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
import numpy
import pixiedust

myLogger = pixiedust.getLogger(__name__)

def append(displayObject, arr, option):
    if option is not None and displayObject.acceptOption(option["name"]):
        arr.append(option)

def chartSize():
    return {
        'name': 'chartsize',
        'description': 'Chart Size',
        'metadata': {
            'type': 'slider',
            'max': 100,
            'min': 50,
            'default': 100
        }
    }

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

def timeSeries(displayObject):
    if len(displayObject.getKeyFields()) == 1:
        pdf = displayObject.getWorkingPandasDataFrame()
        field = displayObject.getKeyFields()[0]
        dtype = pdf[field].dtype.type if field in pdf else None
        existingValue = displayObject.options.get("timeseries", 'false')
        if dtype is not None and (dtype is not numpy.datetime64 or existingValue == 'true'):
            return {
                'name': 'timeseries',
                'description': 'Time Series',
                'metadata':{
                    'type': 'checkbox',
                    'default': 'false'
                }
            }

def barChart(displayObject):
    options = []
    options.append(chartSize())
    options.append(clusterBy(displayObject))
    append(displayObject, options, timeSeries(displayObject))

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

    options.append({
        'name': 'sortby',
        'description': 'Sort By',
        'metadata': {
            'type': 'dropdown',
            'values': ['Keys ASC', 'Keys DESC', 'Values ASC', 'Values DESC'],
            'default': 'Keys ASC'
        }
    })

    return options

def lineChart(displayObject):
    options = []
    options.append(chartSize())
    options.append(clusterBy(displayObject))
    append(displayObject, options, timeSeries(displayObject))

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
            'default': "true"
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
    options.append(chartSize())
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
    default = math.sqrt(count)
    vals = len(displayObject.getWorkingPandasDataFrame().groupby(displayObject.getValueFields()[0]).size())
    options.append({
        'name': 'binsize',
        'description': 'Bin Count',
        'metadata': {
            'type': 'slider',
            'max': int(max(vals, default) + 10),
            'min': int(max((min(vals, default) - 10), 2)),
            'default': int(default)
        }
    })
    return options

def pieChart(displayObject):
    options = []
    options.append(chartSize())

    options.append({
        'name': 'ylabel',
        'description': 'Show y label',
        'metadata': {
            'type': 'checkbox',
            'default': "true"
        }
    })

    return options

def scatterPlot(displayObject):
    options = []
    options.append(chartSize())
    return options

commonOptions = {}
for f in [barChart,lineChart,histogram,pieChart,scatterPlot]:
    commonOptions.update({f.__name__:f})
