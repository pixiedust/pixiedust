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

from abc import abstractmethod
from .display import ChartDisplay
from .plugins.dialog import DialogPlugin
import matplotlib.pyplot as plt
import mpld3
import mpld3.plugins as plugins

class Mpld3ChartDisplay(ChartDisplay):

    def getMpld3Context(self, handlerId):
        return None

    @abstractmethod
    def doRenderMpld3(self, handlerId, figure, axes):
        pass

    def doRender(self, handlerId):
        mpld3.enable_notebook()
        fig, ax = plt.subplots()
        context = self.getMpld3Context(handlerId)
        if (context is not None):
            dialogBody = self.renderTemplate(context[0], **context[1])
        else:
            dialogBody = self.renderTemplate("chartOptionsDialogBody.html")
        plugins.connect(fig, DialogPlugin(self, handlerId, dialogBody))
        return self.doRenderMpld3(handlerId, fig, ax)

	