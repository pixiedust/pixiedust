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

from pixiedust.display.chart.renderers import PixiedustRenderer
from .matplotlibBaseDisplay import MatplotlibBaseDisplay
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from itertools import product
from pyspark.sql import functions as F
import pixiedust
from pixiedust.utils.shellAccess import ShellAccess
from functools import reduce

myLogger = pixiedust.getLogger(__name__)

@PixiedustRenderer(id="barChart")
class BarChartRenderer(MatplotlibBaseDisplay):

    #def getChartContext(self, handlerId):
    #    return ('barChartOptionsDialogBody.html', {})

    def getChartOptions(self):
        if len(self.getKeyFields()) > 1 or len(self.getValueFields()) > 1:
            return [
                {
                    'name': 'stacked',
                    'metadata': {
                        'type': 'checkbox',
                        'default': "false"
                    }
                }
            ]

        return []

    #Main rendering method
    def matplotlibRender(self, fig, ax):
        keyFields = self.getKeyFields()
        valueFields = self.getValueFields()
        stacked = self.options.get("stacked", "true") == "true"

        if len(keyFields) == 1:
            self.getWorkingPandasDataFrame().plot(kind="bar", stacked=stacked, ax=ax, x=keyFields[0], legend=True)
        elif len(valueFields) == 1:
            self.getWorkingPandasDataFrame().pivot(
                index=keyFields[0], columns=keyFields[1], values=valueFields[0]).plot(kind="bar", stacked=stacked, ax=ax, legend=True
            )
        else:
            raise Exception("Cannot have multiple keys and values at the same time")