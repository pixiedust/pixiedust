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

from abc import ABCMeta,abstractmethod
from IPython.display import display as ipythonDisplay, HTML, Javascript
from .constants import *
import sys
import uuid
from collections import OrderedDict

handlers=[]
systemHandlers=[]
defaultHandler=None
globalMenuInfos={}
def registerDisplayHandler(handlerMetadata, isDefault=False, system=False):
    global defaultHandler
    if isDefault and defaultHandler is None:
        defaultHandler=handlerMetadata
    if system:
        systemHandlers.append(handlerMetadata)
    else:
        handlers.append(handlerMetadata)
    
def getSelectedHandler(options, entity):
    if "cell_id" not in options:
        #No cellid, trigger handshake with the browser to get the cellId
        return CellHandshakeMeta()
        
    handlerId=options.get("handlerId")
    if handlerId is not None:
        return globalMenuInfos[handlerId]['handler']
    else:
        if defaultHandler is not None and len(defaultHandler.getMenuInfo(entity))>0:
            return defaultHandler
        #get the first handler that can render this object
        for handler in handlers:
            menuInfos = handler.getMenuInfo(entity)
            if ( menuInfos is not None and len(menuInfos)>0 ):
                return handler
    #we didn't find any, return the first
    return handlers[0]
  
def addId(func):
    def wrapper(*args,**kwargs):
        global globalMenuInfos
        menuInfos = func(*args, **kwargs)
        for menuInfo in menuInfos:
            if 'id' not in menuInfo:
                raise Exception("MenuInfo json must have a unique id")            
            globalMenuInfos[menuInfo['id']]=menuInfo
            menuInfo['handler']=args[0]
        return menuInfos
    return wrapper

class DisplayHandlerMeta(object):
    __metaclass__ = ABCMeta
    @abstractmethod
    @addId
    def getMenuInfo(self):
        pass
    @abstractmethod
    def newDisplayHandler(self,options,entity):
        pass
    
class Display(object):
    __metaclass__ = ABCMeta
    
    def __init__(self, options, entity):
        self.entity=entity
        self.options=options
        self.html=""
        self.scripts=list()
        self.noChrome="handlerId" in options
    
    def render(self):
        handlerId=self.options.get("handlerId")
        if handlerId is None:
            #get the first menuInfo for this handler and generate a js call
            menuInfos = self.handlerMetadata.getMenuInfo(self.entity)
            if len(menuInfos)>0:
                self._addHTML("""
                    <script>
                    ({0})();
                    </script>
                """.format(self._getExecutePythonDisplayScript(menuInfos[0])))
        else:
            self.doRender(handlerId)
            
        #generate final HTML
        ipythonDisplay(HTML(self._wrapBeforeHtml() + self.html + self._wrapAfterHtml()))
        self._addScriptElements()
         
    @abstractmethod
    def doRender(self, handlerId):
        raise Exception("doRender method not implemented")
        
    def _addHTML(self, fragment):
        self.html+=fragment        
        
    def _safeString(self, s):
        if not isinstance(s, str if sys.version >= '3' else basestring):
            return str(s)
        else:
            return s.encode('ascii', 'ignore')
        
    #def _addD3Script2(self):
    #    print("Adding d3")
    #    self._addScriptElement("//cdnjs.cloudflare.com/ajax/libs/d3/3.4.8/d3.min")
        
    def _addScriptElement(self, script,checkJSVar=None, callback=None):
        self.scripts.append((script,checkJSVar,callback))
        
    def _addScriptElements(self):
        if len(self.scripts)==0:
            return
        code="""
            (function(){
                var g,s=document.getElementsByTagName('script')[0];
                function hasScriptElement(script){
                    var scripts = document.getElementsByTagName('script');
                    for (var i=0;i<scripts.length;i++){
                        if(scripts[i].src===script){
                            return true;
                        }
                    }
                    return false;
                }
                var callback;               
        """
        for t in self.scripts:
            script=t[0]
            var=t[1]
            callback=t[2]
            code+="""
            callback = function(){{
                {2}
            }};
            if ({1} && !hasScriptElement('{0}')){{
                g=document.createElement('script');
                g.type='text/javascript';
                g.defer=false; 
                g.async=false; 
                g.src='{0}';
                g.onload = g.onreadystatechange = callback;
                s=s.parentNode.insertBefore(g,s).nextSibling;
            }}else{{
                callback();
            }}
            """.format(script, "true" if var is None else ("typeof "+var + "=='undefined'"), callback or "")
        code+="})();"
        ipythonDisplay(Javascript(code))
    
    def _wrapBeforeHtml(self):
        if self.noChrome:
            return ""        
        menuTree=OrderedDict()
        for catId in ActionCategories.CAT_INFOS.keys():
            menuTree[catId]=[]    
        for handler in (handlers+systemHandlers):
            for menuInfo in handler.getMenuInfo(self.entity):
                categoryId=menuInfo['categoryId']
                if categoryId is None:
                    raise Exception("Handler missing category id")
                elif not categoryId in menuTree:
                    menuTree[categoryId]=[menuInfo]
                else:
                    menuTree[categoryId].append(menuInfo) 
        
        html="""
            <div class="btn-group" role="group" style="margin-bottom:4px">
        """
        for key, menuInfoList in menuTree.iteritems():
            if len(menuInfoList)==1:
                html+="""
                    <a class="btn btn-small btn-default display-type-button" id="menu{0}" title="{1}">
                        <i class="fa {2}"></i>
                    </a>
                    {3}
                """.format(self.getPrefix(menuInfoList[0]), menuInfoList[0]['title'], menuInfoList[0]['icon'], self._getMenuHandlerScript(menuInfoList[0]))
            elif len(menuInfoList)>1:
                html+="""
                    <div class="btn-group btn-small" style="padding-left: 4px; padding-right: 4px;">
                        <a class="btn btn-small display-type-button btn-default" title="{0}" style="text-decoration:none">
                            <i class="fa {1}"></i>
                        </a>
                        <a class="btn btn-small dropdown-toggle btn-default" data-toggle="dropdown">
                            <b class="caret"></b>
                        </a>
                        <div class="dropdown-menu" role="menu">
                            <div class="row-fluid" style="width: 220px;">
                                <ul class="span6 multicol-menu">
                """.format(self.getCategoryTitle(key), self.getCategoryIconClass(key))
                for menuInfo in menuInfoList:                    
                    html+="""
                                    <li>
                                        <a href="#" class="display-type-button" id="menu{0}" style="text-decoration:none">
                                            <i class="fa {1}"></i>
                                            {2}
                                        </a>
                                        {3}
                                    </li>
                    """.format(self.getPrefix(menuInfo), menuInfo['icon'],menuInfo['title'], self._getMenuHandlerScript(menuInfo))
                html+="""
                                </ul>
                            </div>
                        </div>
                    </div>
                """
        html+="""
            </div>
            <div id="wrapperJS{0}"></div>
            <div id="wrapperHTML{0}" style="min-height:100px">
        """.format(self.getPrefix())
        return html
    
    def getPrefix(self, menuInfo=None):
        if ( not hasattr(self, 'prefix') ):
            self.prefix = str(uuid.uuid4())[:8]
        return self.prefix if menuInfo is None else (self.prefix + "-" + menuInfo['id'])
    
    def _getExecutePythonDisplayScript(self, menuInfo=None):
        return """
            function () {{
                cellId = typeof cellId === "undefined" ? "" : cellId;
                var curCell=IPython.notebook.get_cells().filter(function(cell){{return cell.cell_id=="{2}".replace("cellId",cellId);}});
                curCell=curCell.length>0?curCell[0]:null;
                console.log("curCell",curCell);
                //Resend the display command
                var callbacks = {{
                    iopub:{{
                        output:function(msg){{
                            if ({3}){{
                                return curCell.output_area.handle_output.apply(curCell.output_area, arguments);
                            }}
                            var msg_type=msg.header.msg_type;
                            var content = msg.content;
                            if(msg_type==="stream"){{
                                $('#wrapperHTML{0}').html(content.text);
                            }}else if (msg_type==="display_data" || msg_type==="execute_result"){{
                                var html=null;                                    
                                if (!!content.data["text/html"]){{
                                    html=content.data["text/html"];
                                }}else if (!!content.data["image/png"]){{
                                    html=html||"";
                                    html+="<img src='data:image/png;base64," +content.data["image/png"]+"'></img>";
                                }} 
                                                               
                                if (!!content.data["application/javascript"]){{
                                    $('#wrapperJS{0}').html("<script type=\\\"text/javascript\\\">"+content.data["application/javascript"]+"</s" + "cript>");
                                }}
                                
                                if (html){{
                                    if(curCell&&curCell.output_area&&curCell.output_area.outputs){{
                                        var data = JSON.parse(JSON.stringify(content.data));
                                        if(!!data["text/html"])data["text/html"]=html;
                                        curCell.output_area.outputs.push({{"data": data,"metadata":content.metadata,"output_type":msg_type}});
                                    }}
                                    $('#wrapperHTML{0}').html(html);
                                }}
                            }}else if (msg_type === "error") {{
                                require(['base/js/utils'], function(utils) {{
                                    var tb = content.traceback;
                                    console.log("tb",tb);
                                    if (tb && tb.length>0){{
                                        var data = tb.reduce(function(res, frame){{return res+frame+'\\n';}},"");
                                        console.log("data",data);
                                        data = utils.fixConsole(data);
                                        data = utils.fixCarriageReturn(data);
                                        data = utils.autoLinkUrls(data);
                                        $('#wrapperHTML{0}').html("<pre>" + data +"</pre>");
                                    }}
                                }});
                            }}
                            console.log("msg", msg);
                        }}
                    }}
                }}
                
                if (IPython && IPython.notebook && IPython.notebook.session && IPython.notebook.session.kernel){{
                    var command = "{1}".replace("cellId",cellId);
                    console.log("Running command",command);
                    if(curCell&&curCell.output_area)curCell.output_area.outputs=[];
                    $('#wrapperJS{0}').html("")
                    $('#wrapperHTML{0}').html('<div style="width:100px;height:60px;left:47%;position:relative"><i class="fa fa-circle-o-notch fa-spin" style="font-size:48px"></i></div>'+
                    '<div style="text-align:center">Loading your data. Please wait...</div>');
                    IPython.notebook.session.kernel.execute(command, callbacks, {{silent:false,store_history:false,stop_on_error:true}});
                }}
            }}
        """.format(self.getPrefix(), self._genDisplayScript(menuInfo),self.options.get("cell_id","cellId"), "false" if "cell_id" in self.options else "true")
        
    def _getMenuHandlerScript(self, menuInfo):
        return """
            <script>
                $('#menu{0}').on('click', {1})
            </script>
        """.format(self.getPrefix(menuInfo),self._getExecutePythonDisplayScript(menuInfo))
        
    def _genDisplayScript(self, menuInfo=None,addOptionDict={}):
        k=self.callerText.rfind(")")
        retScript = self.callerText[:k]
        if menuInfo:
            retScript+= ",handlerId='"+menuInfo['id'] + "'"
        if "cell_id" not in self.options:
            retScript+= ",cell_id='cellId'"
        for key,value in addOptionDict.iteritems():
            retScript+=","+key+"='"+value+"'"
        retScript+= self.callerText[k:]
        return retScript.replace("\"","\\\"")
        
    def getCategoryTitle(self,catId):
        if catId in ActionCategories.CAT_INFOS:
            return ActionCategories.CAT_INFOS[catId]['title']
        elif catId == "Download":
            return "Stash dataset"
        return ""
            
    def getCategoryIconClass(self,catId):
        if catId in ActionCategories.CAT_INFOS:
            return ActionCategories.CAT_INFOS[catId]['icon-class']
        elif catId == "Download":
            return "fa-cloud-download"
        return ""
        
    def _wrapAfterHtml(self):
        if ( self.noChrome ):
            return ""
        return "</div>"

#Special handler for fetching the id of the cell being executed 
class CellHandshakeMeta(DisplayHandlerMeta):
    def getMenuInfo(self,entity):
       return []
    def newDisplayHandler(self,options,entity):
        return CellHandshake(options,entity)
        
class CellHandshake(Display):
    def render(self):
        ipythonDisplay(HTML("""<script>
            //Marker {0}
            setTimeout(function(){{
                var cells=IPython.notebook.get_cells().filter(function(cell){{
                    if(!cell.output_area || !cell.output_area.outputs){{
                        return false;
                    }}
                    return cell.output_area.outputs.filter(function(output){{
                        if (output.output_type==="display_data"&&output.data&&output.data["text/html"]){{
                            return output.data["text/html"].includes("//Marker {0}")
                        }}
                        return false;
                    }}).length > 0;
                }});
                if(cells.length>0){{
                    var cell=cells[0];
                    var cellId=cell.cell_id;
                    cell.output_area.clear_output(false, true);
                    var old_msg_id = cell.last_msg_id;
                    if (old_msg_id) {{
                        cell.kernel.clear_callbacks_for_msg(old_msg_id);
                    }}
                    !{1}()
                }}else{{
                    alert("An error occurred, unable to access cell id");
                }}
            }},500);
        </script>""".format(self.getPrefix(),self._getExecutePythonDisplayScript() )
        ))
        
    def doRender(self, handlerId):
        pass
