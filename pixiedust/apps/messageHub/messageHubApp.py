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

from pixiedust.display.app import *
from pixiedust.display.streaming.data import *
from pixiedust.display.streaming.bokeh import *
from pixiedust.utils import Logger
import requests

useConfluent = False

@PixieApp
@Logger()
class MessageHubStreamingApp():
    def setup(self):
        self.streamingDisplay = None
        self.streamingData = None
        self.contents = []
        self.schemaX = None
        self.capturing = False
        self.captureVarName = "messageHubData"

    def newDisplayHandler(self, options, entity):
        if self.streamingDisplay is None:
            self.streamingDisplay = LineChartStreamingDisplay(options, entity)
        else:
            self.streamingDisplay.options = options
        return self.streamingDisplay
    
    def getTopics(self):
        rest_endpoint = "https://kafka-rest-prod01.messagehub.services.us-south.bluemix.net:443"
        headers = {
            'X-Auth-Token': self.credentials["api_key"],
            'Content-Type': 'application/json'
        }        
        response = requests.get('{}/topics'.format(rest_endpoint),headers = headers)
        if response.status_code != requests.codes.ok:
            response.raise_for_status()
        return response.json()
    
    @route()
    def mainScreen(self):
        return """
<div class="well" style="text-align:center">
    <div style="font-size:x-large">MessageHub Streaming Browser.</div>
    <div style="font-size:large">Click on a topic to start</div>
</div>

{%for topic in this.getTopics()%}
    {%if loop.first or ((loop.index % 4) == 1)%}
<div class="row">
    <div class="col-sm-2"/>
    {%endif%}
    <div pd_options="topic=$val(topic{{loop.index}}{{prefix}})" class="col-sm-2" style="border: 1px solid lightblue;margin: 10px;border-radius: 25px;cursor:pointer;
        min-height: 150px;background-color:#e6eeff;display: flex;align-items: center;justify-content:center">
        <span id="topic{{loop.index}}{{prefix}}">{{topic}}</span>
    </div>
    {%if loop.last or ((loop.index % 4) == 0)%}
    <div class="col-sm-2"/>
</div>
    {%endif%}
{%endfor%}
        """
    
    def displayNextTopics(self):
        payload = self.streamingData.getNextData()
        if payload is not None and len(payload)>0:
            self.contents = self.contents + payload
            self.contents = self.contents[-10:]                
            html = ""
            for event in self.contents:
                html += "{}<br/>".format(json.dumps(event))
            print(html)
            
    @route(topic="*",streampreview="*",schemaX="*")
    def showChart(self, schemaX):
        self.schemaX = schemaX
        self.avgChannelData = self.streamingData.getStreamingChannel(self.computeAverages)
        return """
<div class="well" style="text-align:center">
    <div style="font-size:x-large">Real-time chart for {{this.schemaX}}(average).</div>
</div>
<style>
.bk-root{
display:flex;
justify-content:center;
}
</style>
<div pd_refresh_rate="1000" pd_entity="avgChannelData"></div>
        """
    
    def computeAverages(self, avg, newData):
        newValue = []
        for jsonValue in newData:
            if self.schemaX in jsonValue:
                thisValue = float(jsonValue[self.schemaX])
                avg = thisValue if avg is None else (avg + thisValue)/2
                newValue.append(avg)
        return newValue, avg
    
    def captureDataInNotebook(self, acc, newData):
        if self.capturing:
            for jsonValue in newData:
                ShellAccess[self.captureVarName].append(jsonValue)
        return None,None
    
    def toggleCapture(self):
        self.capturing = not self.capturing
        if self.capturing:
            capturedData = ShellAccess[self.captureVarName]
            if capturedData is None:
                ShellAccess[self.captureVarName] = []
                capturedData = ShellAccess[self.captureVarName]
            
        print("Capturing in var messageHubData... Click to stop" if self.capturing else "Capture Data")        
    
    @route(topic="*",streampreview="*")
    def createStreamWidget(self, streampreview):
        if streampreview=="realtimeChart":
            return """
<div>
    {%for key in this.streamingData.schema%}
    {%if loop.first%}
    <div class="well" style="text-align:center">
        <div style="font-size:x-large">Create a real-time chart by selecting a field.</div>
    </div>
    {%endif%}
    <div class="radio" style="margin-left:20%">
      <label>
          <input type="radio" pd_options="streampreview=""" + streampreview + """;schemaX=$val(schemaX{{loop.index}}{{prefix}})" 
              id="schemaX{{loop.index}}{{prefix}}" pd_target="realtimeChartStreaming{{prefix}}" 
              name="schemaX" value="{{key}}">{{key}}
      </label>
    </div>
    {%endfor%}
</div>"""
        return """<div pd_refresh_rate="1000" pd_script="self.displayNextTopics()"></div>"""
        
    @route(topic="*")
    def previewTopic(self, topic):
        self.topic = topic
        if self.streamingData is not None:
            self.streamingData.close()
        Adapter = MessagehubStreamingAdapter
        if useConfluent:
            from pixiedust.display.streaming.data.messageHubConfluent import MessagehubStreamingAdapterConfluent
            Adapter = MessagehubStreamingAdapterConfluent
            self.debug("Using Confluent Kafka")
        self.streamingData = Adapter( self.topic, self.credentials["username"], self.credentials["password"], self.credentials.get("prod", True) )
        self.streamingData.getStreamingChannel(self.captureDataInNotebook)
        return """
<div class="well" style="text-align:center">
    <div style="font-size:x-large">Preview raw JSON Data from MessageHub.</div>
    <div id="tools{{prefix}}" style="text-align:center">
        <button type="button" class="btn btn-default" pd_target="captureBtn{{prefix}}">
            <span class="no_loading_msg" id="captureBtn{{prefix}}">Capture Data</span>
            <pd_script>self.toggleCapture()</pd_script>
        </button>
    </div>
</div>
<div class="row">
    <div class="col-sm-12" id="targetstreaming{{prefix}}">
        <div pd_refresh_rate="1000" style="white-space:nowrap;overflow-x:auto;border:aliceblue 2px solid;height:17em;line-height:1.5em">
            <pd_script>self.displayNextTopics()</pd_script>
            <div style="width:100px;height:60px;left:47%;position:relative">
                <i class="fa fa-circle-o-notch fa-spin" style="font-size:48px"></i>
            </div>
            <div style="text-align:center">Waiting for data from MessageHub</div>
        </div>
    </div>
</div>
<div class="row" id="realtimeChartStreaming{{prefix}}">
    <div pd_refresh_rate="4000" pd_options="streampreview=realtimeChart">
    </div>
</div>
        """