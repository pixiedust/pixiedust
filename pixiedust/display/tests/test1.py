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

from ..display import Display
import matplotlib.pyplot as plt
import numpy as np
import warnings
    
class Test1Display(Display):
    def doRender(self, handlerId):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import mpld3
            mpld3.enable_notebook()        
        
            fig, ax = plt.subplots(subplot_kw=dict(axisbg='#EEEEEE'))
            ax.grid(color='white', linestyle='solid')

            N = 50
            scatter = ax.scatter(np.random.normal(size=N),
                        np.random.normal(size=N),
                        c=np.random.random(size=N),
                        s = 1000 * np.random.random(size=N),
                        alpha=0.3,
                        cmap=plt.cm.jet)

            ax.set_title("D3 Scatter Plot", size=18);