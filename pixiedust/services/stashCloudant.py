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

from ..display.display import Display
import time
import requests

class StashCloudantHandler(Display):
    def doRender(self, handlerId):
        entity=self.entity

        dbName = self.options.get("dbName", "dataframe-"+time.strftime('%m%d%Y-%l%M'))
        doStash=self.options.get("doStash")
        if doStash is None: 
            self._addHTML("""
                <script>
                    require(['base/js/dialog'],function(dialog){{
                        var modal = dialog.modal;
                        var modal_obj = modal({{
                            title: "Stash to Cloudant",
                            body: '{0}',
                            sanitize:false,
                            notebook: IPython.notebook,
                            keyboard_manager: IPython.notebook.keyboard_manager,
                            buttons: {{
                                OK: {{
                                    class : "btn-primary",
                                    click: function() {{
                                        var callbacks = {2};
                                        $('#loading{3}').css('display','block');
                                        IPython.notebook.session.kernel.execute(
                                            "{1}", 
                                            callbacks, 
                                            {{silent:false,store_history:false,stop_on_error:true}}
    	                                );
                                    }}
                                }},
                                Cancel: {{}}
                            }}
                        }});
                        modal_obj.on('shown.bs.modal', function(){{
                            $("#service-connection-group .dropdown-menu li a").click(function(){{
                                $('#service-connection').html($(this).text()+' <span class="caret"></span>');
                            }});
                            $("#add-service-connection").click(function(){{
                                alert("Here goes the add Cloudant Connection dialog");
                            }});
                        }});
                    }})
                </script>
                <div id="loading{3}" style="display:none">
                    <div style="width:100px;height:60px;left:47%;position:relative">
                        <i class="fa fa-circle-o-notch fa-spin" style="font-size:48px"></i>
                    </div>
                    <div style="text-align:center">Stashing your data in Cloudant. Please wait...</div>
                </div>
                <div id="results{3}"></div>
            """.format(
                self._getServiceDialogBody(dbName),
                self._genDisplayScript(addOptionDict={'doStash':'True','dbName':dbName}),
                self._getCallbackScript(),
                self.getPrefix()
            ))
        else:
            #first create the stash db
            r = requests.put("http://dtaieb:password@127.0.0.1:5984/" + dbName )
            if ( r.status_code != 200 and r.status_code != 201 ):
                print("Unable to create db: " + str(r.content) )
            else:
                self.entity.write.format("com.cloudant.spark")\
                    .option("cloudant.host", "http://127.0.0.1:5984")\
                    .option("cloudant.username","dtaieb")\
                    .option("cloudant.password","password")\
                    .option("createDBOnSave","true")\
                    .save(dbName)
                print("""Successfully stashed your data: <a target='_blank' href='http://127.0.0.1:5984/{0}'>{0}</a>""".format(dbName))

    def _getCallbackScript(self):
        return """
            {{
                iopub:{{
                    output:function(msg){{
                        var msg_type=msg.header.msg_type;
                        var content = msg.content;
                        if(msg_type==="stream"){{
                            $('#results{0}').html(content.text);
                            $('#loading{0}').css('display','none');
                        }}else if (msg_type==="display_data" || msg_type==="execute_result"){{
                            //alert("got data", content.data["text/html"]);
                            if (!!content.data["text/html"]){{
                                //$('#results{0}').html(content.data["text/html"]);
                            }}
                        }}else if (msg_type === "error") {{
                            require(['base/js/utils'], function(utils) {{
                                var tb = content.traceback;
                                if (tb && tb.length>0){{
                                    var data = tb.reduce(function(res, frame){{return res+frame+'\\n';}},"");
                                    data = utils.fixConsole(data);
                                    data = utils.fixCarriageReturn(data);
                                    data = utils.autoLinkUrls(data);
                                    $('#loading{0}').html("<pre>" + data +"</pre>");
                                }}
                            }});
                        }}
                    }}
                }}
            }}
        """.format(self.getPrefix())
    def _getServiceDialogBody(self,dbName):
        return self._oneLine("""
            <form class="form-horizontal" role="form">
                <div class="form-group">
                    <label class="control-label col-sm-3" for="pwd">Cloudant Connection:</label>
                <div class="col-sm-9" >
                    <div class="input-group" id="service-connection-group" style="width:100%" > 
                        <a class="btn btn-default dropdown-toggle btn-select" id="service-connection" style="width:100%" data-toggle="dropdown" href="#">
                            Select a Service connection
                            <span class="caret"></span>
                        </a>
                        <span class="input-group-addon" id="add-service-connection" style="cursor:pointer">+</span>
                        <ul class="dropdown-menu" style="width:100%" >
                            <li><a href="#">Cloudant-XY1</a></li>
                            <li><a href="#">Cloudant-XY2</a></li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-3">Database:</label>
                <div class="col-sm-9">
                    <input type="text" class="form-control" id="dbName" readonly value="{0}">
                </div>
            </div>
        </form>'
        """.format(dbName)\
           .replace("'","\\'"))
    
    @classmethod
    def _oneLine(cls, s):
        return reduce(lambda s, l: s+l, s.split("\n"), "")