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
defaultHandler=None
globalMenuInfos={}
def registerDisplayHandler(handlerMetadata, isDefault=False):
    global defaultHandler
    if isDefault and defaultHandler is None:
        defaultHandler=handlerMetadata        
    handlers.append(handlerMetadata)
    
def getSelectedHandler(handlerId, entity):
    if handlerId is not None:
        return globalMenuInfos[handlerId]['handler']
    else:
        if defaultHandler is not None:
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
    def newDisplayHandler(self,handlerId,entity):
        pass
    
class Display(object):
    __metaclass__ = ABCMeta
    
    def __init__(self, entity):
        self.entity=entity
        self.html=""
        self.scripts=list()
    
    def render(self, handlerId):
        self.doRender(handlerId)
        #generate final HTML
        ipythonDisplay(HTML(self._wrapBeforeHtml() + self.html + self._wrapAfterHtml()))
        self._addScriptElements()
         
    @abstractmethod
    def doRender(self, handlerId):
        raise Exception("doRender method not implemented")
    
    def noChrome(self, flag):
        self.noChrome=flag
        
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
        
    def _addScriptElement(self, script):
        self.scripts.append(script)
        
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
        """
        for script in self.scripts:
            code+="""
            if (!hasScriptElement('{0}')){{
                g=document.createElement('script');
                g.type='text/javascript';
                g.defer=false; 
                g.async=false; 
                g.src='{0}';
                s=s.parentNode.insertBefore(g,s).nextSibling;
            }}
            """.format(script)
        code+="})();"
        ipythonDisplay(Javascript(code))
    
    def _wrapBeforeHtml(self):
        if self.noChrome:
            return ""
        
        menuTree=OrderedDict()
        for catId in ActionCategories.CAT_INFOS.keys():
            menuTree[catId]=[]    
        for handler in handlers+[DownloadMeta()]:
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
            <div id="wrapperHTML{0}">
        """.format(self.getPrefix())
        return html
    
    def getPrefix(self, menuInfo=None):
        if ( not hasattr(self, 'prefix') ):
            self.prefix = str(uuid.uuid4())[:8]
        return self.prefix if menuInfo is None else (self.prefix + "-" + menuInfo['id'])
        
    def _getMenuHandlerScript(self, menuInfo):
        return """
            <script>
                $('#menu{0}').on('click', function () {{
                    //Resend the display command
                    var callbacks = {{
                        iopub:{{
                            output:function(msg){{
                                var msg_type=msg.header.msg_type;
                                var content = msg.content;
                                if(msg_type==="stream"){{
                                    $('#wrapperHTML{1}').html(content.text);
                                }}else if (msg_type==="display_data" || msg_type==="execute_result"){{
                                    if (content.data["text/html"]){{
                                        $('#wrapperHTML{1}').html(content.data["text/html"]);
                                    }}                                    
                                    if (content.data["application/javascript"]){{
                                        $('#wrapperJS{1}').html("<script type=\\\"text/javascript\\\">"+content.data["application/javascript"]+"</s" + "cript>");
                                    }}
                                }}else if (msg_type === "error") {{
                                    var errorHTML="<p>"+content.ename+"</p>";
                                    errorHTML+="<p>"+content.evalue+"</p>";
                                    errorHTML+="<pre>" + content.traceback+"</pre>";
                                    $('#wrapperHTML{1}').html(errorHTML);
                                }}
                                console.log("msg", msg);
                            }}
                        }}
                    }}
                    
                    console.log("Running command: {2}");
                    $('#wrapperJS{1}').html("")
                    $('#wrapperHTML{1}').html('<div style="width:100px;height:60px;left:47%;position:relative"><i class="fa fa-circle-o-notch fa-spin" style="font-size:48px"></i></div>'+
                    '<div style="text-align:center">Loading your data. Please wait...</div>');
                    IPython.notebook.session.kernel.execute("{2}", callbacks, {{silent:false, store_history:false}});
                }})
            </script>
        """.format(self.getPrefix(menuInfo), self.getPrefix(), self._genDisplayScript(menuInfo))
        
    def _genDisplayScript(self, menuInfo):
        k=self.callerText.rfind(")")
        return self.callerText[:k]+",handlerId='"+menuInfo['id'] + "'" + self.callerText[k:]
        
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
        
        
class DownloadMeta(DisplayHandlerMeta):
    @addId
    def getMenuInfo(self,entity):
        clazz = entity.__class__.__name__
        if clazz == "DataFrame":
            return [
                {"categoryId": "Download", "title": "Download as CSV", "icon": "fa-download", "id": "downloadCSV"},
                {"categoryId": "Download", "title": "Stash to Cloudant", "icon": "fa-cloud", "id": "downloadCloudant"},
                {"categoryId": "Download", "title": "Stash to Object Storage", "icon": "fa-suitcase", "id": "downloadSwift"}
            ]
        else:
            return []
    def newDisplayHandler(self,entity):
        return DownloadHandler(entity)

class DownloadHandler(Display):
    def doRender(self, handlerId):
        entity=self.entity
            
        self._addHTML("""
            <p><b>Sorry, but download is not yet implemented. Please check back often!</b></p>
        """
        )
