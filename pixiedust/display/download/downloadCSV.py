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
import time

EOF="@#$EOF@#$"

class DownloadCSVHandler(Display):
    def doRender(self, handlerId):
        entity=self.entity
        
        doDownload=self.options.get("doDownload")
        if doDownload is None:    
            self._addHTML("""<script>
                var blobs = [];
                var callbacks = {{
                    iopub:{{
                        output:function(msg){{
                            var msg_type=msg.header.msg_type;
                            var content = msg.content;
                            if(msg_type==="stream"){{
                                console.log("Got Data", content.text);
                                var s = content.text.split("\\n");
                                for ( var i = 0; i < s.length; i++ ){{
                                    if(s[i]==="{1}"){{
                                        console.log("Starting download");
                                        var URL = (window.webkitURL || window.URL);
                                        var url = URL.createObjectURL(new Blob(blobs, {{type : "text/plain"}}));
                                        var a = document.createElement('a');
                                        a.setAttribute('href', url);
                                        a.setAttribute('download', "{2}.csv");
                                        a.click();
                                        return URL.revokeObjectURL(url);
                                    }}else{{
                                        blobs.push(new Blob([s[i]+"\\n"], {{type : "text/plain"}}));
                                    }}
                                }}
                            }}else if (msg_type === "error") {{
                                alert("An error occurred: " + content.ename);
                            }}
                        }}
                    }}
                }};

                IPython.notebook.session.kernel.execute(
                    "{0}", 
                    callbacks, {{silent:false,store_history:false,stop_on_error:true}}
                );
                
                console.log("running download command: {0}");
            </script>""".format(self._genDisplayScript(addOptionDict={'doDownload':'True'}),EOF,"dataframe-"+time.strftime('%m%d%Y-%l%M'))
            )
        else:
            #write headers first
            schema = entity.schema
            print(reduce(lambda s,f: s + ("," if s!="" else "") + f.name, schema.fields,""))                
            for row in entity.take(100):
                print( reduce(lambda s,f: s+("," if s!="" else "")+self._safeString(row[f.name]),schema.fields, ""))
            print(EOF)