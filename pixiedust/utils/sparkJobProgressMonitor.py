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
from pixiedust.utils.template import PixiedustTemplateEnvironment
from IPython.core.getipython import *
from IPython.display import display, HTML, Javascript
from pixiedust.utils.shellAccess import ShellAccess
import uuid
import json
import sys
import traceback

_env = PixiedustTemplateEnvironment()
progressMonitor = None

def enableSparkJobProgressMonitor():
    global progressMonitor
    if progressMonitor is None:
        progressMonitor = SparkJobProgressMonitor()

class SparkJobProgressMonitorOutput(object):
    class Java:
        implements = ["com.ibm.pixiedust.PixiedustOutputListener"]
    
    def __init__(self):
        self.firstTime=True
        self.updaterId = "updaterId"
        self.progressHTMLId = "progress"
        self.currentJobId = None

    def display_with_id(self, obj, display_id, update=False):
        """Create a new display with an id"""
        ip = get_ipython()
        data, md = ip.display_formatter.format(obj)
        transient = {'display_id': display_id}
        content = {
            'data': data,
            'metadata': md,
            'transient': transient,
        }
        msg_type = 'update_display_data' if update else 'display_data'
        ip.kernel.session.send(ip.kernel.iopub_socket, msg_type, content, parent=ip.parent_header)

    def printOutput(self, s):
        self.printStuff(s)
        self.updaterId = "updaterId"
        self.progressHTMLId = "progress"        

    def sendChannel(self, channel, data):
        self.printStuff(channel, data)

    def onRunCell(self):
        self.firstTime = True
        self.prefix = str(uuid.uuid4())[:8]
        self.updaterId = "updaterId{0}".format(self.prefix)
        self.progressHTMLId = "progress{0}".format(self.prefix)
        #Create the place holder area for the progress monitor
        self.display_with_id( HTML( """
            <div id="pm_container{0}">
                <ul class="nav nav-tabs" id="progressMonitors{0}">
                </ul>
                <div class="tab-content" id="tabContent{0}">
                </div>
            </div>""".format(self.prefix)
            ),self.progressHTMLId )

    def printStuff(self,channel, s):
        if True:
            try:
                if channel=="jobStart": 
                    data = json.loads(s)
                    self.currentJobId=data["jobId"]
                    display(
                        Javascript(_env.getTemplate("sparkJobProgressMonitor/addJobTab.js").render( prefix=self.prefix, data=data ) )
                    )
                elif False and channel=="stageSubmitted":
                    data=json.loads(s)
                    self.display_with_id( HTML(addStage.format(
                        jobId=self.currentJobId,stageId=data["stageInfo"]["stageId"],numTasks=data["stageInfo"]["numTasks"],
                        details=data["stageInfo"]["details"]
                    )), self.updaterId, update=True)
                elif channel=="taskStart":
                    data=json.loads(s)
                    display(
                        Javascript(_env.getTemplate("sparkJobProgressMonitor/taskStart.js").render( prefix=self.prefix, data=data ) )
                    )
                elif channel=="stageCompleted":
                    data=json.loads(s)
                    #self.display_with_id( HTML( updateDetails.format(
                    #    stageId=data["stageId"], numTask=data["taskInfo"]["index"]+1
                    #)), updaterId, update=True)
            except:
                print("Unexpected error: {0} : {1}".format(s, sys.exc_info()[0]))
                traceback.print_exc()
        else:        
            self.display_with_id( HTML(gs), self.progressHTMLId, update= not firstTime)

class SparkJobProgressMonitor(object):
    def __init__(self):
        self.addSparkListener()

    def addSparkListener(self):
        get_ipython().run_cell_magic(
            "scala",
            "cl=sparkProgressMonitor",
            _env.getTemplate("sparkJobProgressMonitor/addSparkListener.scala").render()
        )

        listener = get_ipython().user_ns.get("__pixiedustSparkListener")

        #access the listener object from the namespace
        if listener:
            monitorOutput = SparkJobProgressMonitorOutput()
            #Add pre_run_cell event handler
            get_ipython().events.register('pre_run_cell',lambda: monitorOutput.onRunCell() )
            listener.setChannelListener( monitorOutput )
