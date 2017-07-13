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
from repository.mlrepositoryclient import MLRepositoryClient
from repository.mlrepositoryartifact import MLRepositoryArtifact
from pixiedust.utils.shellAccess import ShellAccess

@PixieApp
class WatsonMLApp():    
    def initWatsonML(self):
        credentials = self.getPixieAppEntity()
        if credentials is None:
            return "<div>You must provide credentials to your Watson ML Service</div>"
        self.ml_repository_client = MLRepositoryClient(credentials['service_path'])
        self.ml_repository_client.authorize(credentials['username'], credentials['password'])
        
    def downloadModel(self, modelId):
        ShellAccess["mlModel"] = self.ml_repository_client.models.get(modelId).model_instance()
        print("Model successfully downloaded in variable mlModel")
        
    @route()
    def startScreen(self):
        message = self.initWatsonML()
        if message is not None:
            return message

        return """
<style>
.pd_tooltip {
    position: relative;
    display: inline-block;
    border-bottom: 1px dotted black;
}

.pd_tooltip .pd_tooltiptext {
    visibility: hidden;
    background-color: white;
    color: black;
    border: 1px solid black;
    border-radius: 6px;
    padding: 5px 0;
    position: absolute;
    z-index: 1;
    bottom: 125%;
    margin-left: -360px;
    opacity: 0;
    transition: opacity 1s;
}

.pd_tooltip .pd_tooltiptext::after {
    content: "";
    position: absolute;
    top: 100%;
    left: 50%;
    margin-left: -5px;
    border-width: 5px;
    border-style: solid;
    border-color: #555 transparent transparent transparent;
}

.pd_tooltip:hover .pd_tooltiptext {
    visibility: visible;
    opacity: 1;
}
</style>
<div class="well">
    <span style="font-size:x-large">List of Watson ML models</span>
    <button style="float:right" type="submit" class="btn btn-primary">
        Upload a new Model
    </button>
</div>

{%for model in this.ml_repository_client.models.all()%}
    {%if loop.first or ((loop.index % 4) == 1)%}
<div class="row">
    <div class="col-sm-2"/>
    {%endif%}
    <div class="col-sm-2" style="border: 1px solid lightblue;margin: 10px;border-radius: 25px;cursor:pointer;
        min-height: 150px;background-color:#e6eeff;display: flex;align-items: center;">
        <table style="margin-left:15px;width:90%">
            <tr>
                <td style="padding:10px"><b>Model:</b></td>
                <td>{{model.name}}</td>
            </tr>
            <tr>
                <td style="padding:10px"><b>Id:</b></td>
                <td>{{model.uid}}</td>
            </tr>
            <tr>
                <td style="padding:10px"><b>Creation Time:</b></td>
                <td>{{model.meta.prop("creationTime")}}</td>
            </tr>
            <tr>
                <td colspan="2" style="text-align:center">
                    <div class="btn-group">
                        <button type="button" class="btn btn-default" pd_script="self.removeModel('{{model.uid}}')">
                            <i class="fa fa-trash"/>
                        </button>
                        <button type="button" class="btn btn-default" pd_target="message{{loop.index}}{{prefix}}" 
                            pd_script="self.downloadModel('{{model.uid}}')">
                            <i class="fa fa-download"/>
                        </button>
                        <button type="button" class="pd_tooltip btn btn-default">
                            <i class="fa fa-info"/>
                            <span class="pd_tooltiptext">
                                <table>
                                {% for item in model.meta.available_props() if (item != "inputDataSchema" and item !="trainingDataSchema")%}
                                    <tr>
                                        <td><b>{{item}}</b></td>
                                        <td>{{model.meta.prop(item)}}</td>
                                    </tr>
                                {% endfor %}
                                </table>
                            </span>
                        </button>                        
                    </div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div id="message{{loop.index}}{{prefix}}"/>
                </td>
            </tr>
        </table>
    </div>
    {%if loop.last or ((loop.index % 4) == 0)%}
    <div class="col-sm-2"/>
</div>
    {%endif%}
{%endfor%}
"""