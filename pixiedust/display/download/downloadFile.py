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

DELIMITER="@#$DELIMITER@#$"

class DownloadFileHandler(Display):
    def doRender(self, handlerId):
        entity=self.entity
        self.addProfilingTime = False
        total=entity.count()
        schema = entity.schema
        doDownload=self.options.get("doDownload")
        doDownloadCount=self.options.get("doDownloadCount")
        doDownloadLink=self.options.get("doDownloadLink")
        if total==0:
            self._addHTML("<p>No data available for download</p>")
        elif doDownload is None:    
            self._addHTMLTemplate("downloadFile.html", totalDocs=total)
        elif doDownloadLink is None:
            self._addHTML("""<script>
                var blobs = [];
                var callbacks = {{
                    iopub:{{
                        output:function(msg) {{
                            var msg_type = msg.header.msg_type;
                            var content = msg.content;
                            if (msg_type==='stream') {{
                                var s = content.text.split("\\n");
                                if (s[0]==="{1}") {{
                                    for (var i = 1; i < s.length; i++ ) {{
                                        if (s[i]==="{1}") {{
                                            console.log('Starting download');
                                            var URL = (window.webkitURL || window.URL);
                                            var url = URL.createObjectURL(new Blob(blobs, {{type : "text/plain"}}));
                                            var a = document.createElement('a');
                                            a.innerHTML = "{2}.{4}";
                                            a.href = url;
                                            a.download = "{2}.{4}";
                                            
                                            var d = document.createElement('div');
                                            d.style = 'padding: 20px';
                                            d.innerHTML = '<span>File successfully exported for download: </span>';
                                            d.appendChild(a);

                                            document.getElementById('results{3}').innerHTML = '';
                                            document.getElementById('results{3}').appendChild(d);

                                            a.click();
                                            //return URL.revokeObjectURL(url);
                                        }}else{{
                                            blobs.push(new Blob([s[i]+"\\n"], {{type : "text/plain"}}));
                                        }}
                                    }}
                                }}
                                else {{
                                    $('#wrapperHTML{3}').html('<p>' + s.join('<br/>') + '</p>');
                                }}
                            }}
                            else if (msg_type === 'error') {{
                                var d = document.getElementById('wrapperHTML{3}');
                                d.appendChild('<span>Export for download failed: ' + content.ename + '</span>');
                                for (m in msg) console.log('#msg', m, msg[m]);
                            }}
                        }}
                    }}
                }};

                IPython.notebook.session.kernel.execute(
                    "{0}", 
                    callbacks, {{silent:false,store_history:false,stop_on_error:true}}
                );
                
                console.log("running download command: {0}");
            </script>""".format(self._genDisplayScript(addOptionDict={'doDownloadLink':'True'}),DELIMITER,"dataframe-"+time.strftime('%Y%m%d-%H%M%S'),self.getPrefix(), doDownload)
            )
        elif doDownload == "csv":
            #write headers first
            print(DELIMITER)
            print(reduce(lambda s,f: s + ("," if s!="" else "") + f.name, schema.fields,""))                
            for row in entity.take(doDownloadCount):
                print(reduce(lambda s,f: s+("," if s!="" else "")+self._safeString(row[f.name]), schema.fields, ""))
            print(DELIMITER)
        elif doDownload == "json":
            print(DELIMITER)
            print("[")
            for count, row in enumerate(entity.take(doDownloadCount), start=1):
                print(" {")
                print(reduce(lambda s,f: s+(",\n  " if s!="" else "  ")+"\""+self._safeString(f.name)+"\":"+(str(row[f.name]) if isinstance(row[f.name],(int,long, float)) else self._safeString("\""+row[f.name]+"\"")), schema.fields, ""))
                print(" }," if count != doDownloadCount else " }")
            print("]")
            print(DELIMITER)
        elif doDownload == "xml":
            print(DELIMITER)
            print('<?xml version="1.0" encoding="UTF-8"?>')
            print("<dataframe>")
            for count, row in enumerate(entity.take(doDownloadCount), start=1):
                print(" <row>")
                print(reduce(lambda s,f: s+("\n  " if s!="" else "  ")+"<"+self._safeString(f.name.replace (" ", "_"))+">"+self._safeString(row[f.name])+"</"+self._safeString(f.name.replace (" ", "_"))+">", schema.fields, ""))
                print(" </row>")
            print("</dataframe>")
            print(DELIMITER)
        elif doDownload == "html":
            print(DELIMITER)
            print("<table>\n <thead>\n  <tr>")
            print(reduce(lambda s,f: s+("\n   " if s!="" else "   ")+"<th>"+self._safeString(f.name)+"</th>", schema.fields, ""))
            print("  </tr>\n </thead>")
            print(" <tbody>")
            for count, row in enumerate(entity.take(doDownloadCount), start=1):
                print("  <tr>")
                print(reduce(lambda s,f: s+("\n   " if s!="" else "   ")+"<td>"+self._safeString(row[f.name])+"</td>", schema.fields, ""))
                print("  </tr>")
            print(" </tbody>\n</table>")
            print(DELIMITER)
        elif doDownload == "md":
            print(DELIMITER)
            print(reduce(lambda s,f: s+self._safeString(f.name)+"|", schema.fields, "|"))
            print(reduce(lambda s,f: s+"---|", schema.fields, "|"))
            for count, row in enumerate(entity.take(doDownloadCount), start=1):
                print(reduce(lambda s,f: s+self._safeString(row[f.name])+"|", schema.fields, "|"))
            print(DELIMITER)
        elif doDownload == "txt":
            print(DELIMITER)
            print(entity.show(doDownloadCount))
            print(DELIMITER)
        else:
            print("Selected option not implemented")