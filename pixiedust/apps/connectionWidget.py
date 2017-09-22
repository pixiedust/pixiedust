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
from .cfBrowser import CFBrowser
from pixiedust.display.app import *
from pixiedust.services.serviceManager import *
from pixiedust.utils import Logger

@Logger()
class ConnectionWidget(CFBrowser):
    def getConnections(self):
        return getConnections("cloudant")

    def selectBluemixCredentials(self, service_name, credentials_str):
        credentials = json.loads(credentials_str)
        payload = {'name': service_name, 'credentials': credentials}
        addConnection('cloudant', payload)
        self.selectedConnection = payload['name']
        #return self.dataSourcesList()
        return """
<script>
    pixiedust.executeDisplay({{pd_controls}}, {
        'targetDivId': "dummy",
        'script': "import json\\nprint(json.dumps( self.getConnections()))",
        'onError': function(error){
            alert(error);
        },
        'onSuccess': function(results){
            var options = []
            $.each(JSON.parse(results), function(key, value){
                var selected = (value.name=="{{this.selectedConnection}}") ? 'selected="selected"' : "";
                options.push('<option ' + selected + ' value="'+ value.name +'">'+ value.name +'</option>');
            });
            $("#connection{{prefix}}").html(options.join(''));
        }
    });
</script>
        """
    
    @route(selectedConnection="*", editConnection="*")
    def _editConnection(self):
        jsOnLoad = """
var CodeMirror = require('codemirror/lib/codemirror');
function createEditor(content){
    $('#connTextArea{{prefix}}').html('<textarea id="connection-info" rows=13 cols=80 name="connection-info"/>');
    global.editor = CodeMirror.fromTextArea($("#connection-info")[0], {
        lineNumbers: true,
        matchBrackets: true,
        indentUnit: 2,
        autoIndent: true,
        mode: 'application/json'
    });
    global.editor.setSize("100%", 300);
    global.editor.setValue(content);
}
var connectionName = $("#connection{{prefix}}").val();
if ( connectionName ){
    function toJson(v){
        if (!v){
            return ""
        }
        v = JSON.parse(v);
        return JSON.stringify(v, null, '\t');
    }
    var script = "from pixiedust.services.serviceManager import getConnection\\n"+
        "import json\\n"+
        "print( json.dumps( getConnection(\\\"cloudant\\\",\\\"" + connectionName + "\\\", raw=False)))";
    pixiedust.executeDisplay({{pd_controls}}, {
        'targetDivId': "connTextArea{{prefix}}",
        'script': script,
        'onError': function(error){
            $("#connection-error").text(error);
        },
        'onSuccess': function(results){
            createEditor(toJson(results));
        }
    })
}else{
    createEditor('{\\n\\
        "name": "<<cloudant-connection name>>",\\n\\
        "credentials": {\\n\\
            "username": "<<userIdentifier>>-bluemix",\\n\\
            "password": "<<password>>",\\n\\
            "host": "<<hostIdentifier>>-bluemix.cloudant.com",\\n\\
            "port": 443,\\n\\
            "url": "https://<<userIdentifier>>-bluemix:<<password>>@<<hostIdentifier>>-bluemix.cloudant.com"\\n\\
        }\\n\\
    }');
}
        """
        jsOK = """
try {
    var connInfo = JSON.parse(global.editor.getValue());
    var script = "from pixiedust.services.serviceManager import addConnection\\n"+
        "print(addConnection(\\"cloudant\\"," + global.editor.getValue().replace(/[\\n\\r]+/g,"") + "))";
    pixiedust.executeDisplay({{pd_controls}}, {
        'targetDivId': "dummy",
        'script': script,
        'onError': function(error){
            $("#connection-error").text(error);
        },
        'onSuccess': function(results){
            if (typeof editConnCallback != "undefined"){
                editConnCallback(results);
            }
            modal_obj.modal('hide')
        }
    });
    return false;
} catch(e) {
    console.log(e);
    $("#connection-error").text('System error: ' + e.message);
    return false;
}
        """
        body = """
<div class="well">
    Please enter your connection information as JSON in the text area below.
    For a new connection, you can for example copy and paste the service credentials from Bluemix.
</div>
<div id="connection-error" style="color:red"/>
<div id="connTextArea{{prefix}}"/>
        """
        return {"body":body, "jsOnLoad": jsOnLoad, "jsOK":jsOK}
    
    @route(selectedConnection="*", deleteConnection="true")
    def _deleteConnection(self):
        deleteConnection("cloudant", self.selectedConnection)
        self.deleteConnection = "false"
        return self.dataSourcesList()
        
    @route(selectedConnection="*", browseBMConnection="true")
    def _browseBMConnection(self):
        return self.startBrowsingBM()
    
    @route(selectedConnection="*", newConnection="true")
    def _newConnection(self):            
        body = """
<div class="well">
    New Connection
</div>
<div class="container" id="newConnectionContainer{{prefix}}">
    <div class="col-sm-2"/>
    <div class="col-sm-4" style="border: 1px solid lightblue;margin: 10px;border-radius: 25px;cursor:pointer;
        min-height: 150px;text-align: center;background-color:#e6eeff;display: flex;align-items: center;"
        pd_options="manualConnection=true">
        <h2>Enter the connection manually</h2>
    </div>
    <div class="col-sm-4" style="border: 1px solid lightblue;margin: 10px;border-radius: 25px;cursor:pointer;
        min-height: 150px;text-align: center;background-color:#e6eeff;;display: flex;align-items: center;"
        pd_options="browseBMConnection=true">
        <h2>Browse your services on Bluemix</h2>
    </div>
    <div class="col-sm-2"/>
</div>
"""
        return {"body":body, "dialogRoot": "newConnectionContainer{{prefix}}"}
    
    @route(widget="DataSourcesList")
    def dataSourcesList(self):
        num_connections = len(self.getConnections())
        select_conn_script = ' pd_script="self.selectedConnection ='
        if num_connections > 0:
            select_conn_script += "'$val(connection{{prefix}})'\""
        else:
            select_conn_script += '\'none\'"'
        output = """
<div>
    <div class="form-group">
      <label for="connection{{prefix}}" class="control-label col-sm-2">Select a cloudant connection:</label>
      <div class="col-sm-7">
        <select class="form-control" id="connection{{prefix}}">
          {%for conn in this.getConnections() %}
              {%set selected=(this.selectedConnection==conn.name)%}
              <option {%if selected%}selected="selected"{%endif%}  value="{{conn.name|escape}}">{{conn.name|escape}}</option>
          {%endfor%}
        </select>
      </div>
      <div class="col-sm-2 btn-toolbar" role="toolbar">
        <div class="btn-group" role="group\"""" + select_conn_script + """>
"""
        if num_connections > 0:
            output += """
            <button type="button" class="btn btn-default">Go</button>'
            <button type="button" class="btn btn-default" pixiedust pd_options="dialog=true;editConnection=true">
                <i class="fa fa-pencil-square-o"/>
            </button>"""
        output += """
            <button type="button" class="btn btn-default" pixiedust pd_options="dialog=true;newConnection=true">
                <i class="fa fa-plus"/>
            </button>"""
        if num_connections > 0:
            output += """
            <button type="button" class="btn btn-default" pixiedust>
                <pd_script type="preRun">
                    return confirm("Delete " + $("#connection{{prefix}}").val() + "?");
                </pd_script>
                <pd_script>self.deleteConnection="true"</pd_script>
                <i class="fa fa-trash"/>
            </button>
        </div>
      </div>
    </div>
</div>
"""
        return output