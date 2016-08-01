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
from ..utils.template import *
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

    #global jinja2 Environment
    env = PixiedustTemplateEnvironment()
    
    def __init__(self, options, entity):
        self.entity=entity
        self.options=options
        self.html=""
        self.scripts=list()
        self.noChrome="handlerId" in options

    def _getTemplateArgs(self, **kwargs):
        args = {
            "this":self, "entity":self.entity, "prefix":self.getPrefix(),
            "module":self.__module__
        }
        if kwargs:
            args.update(kwargs)
        return args

    def renderTemplate(self, templateName, **kwargs):
        return self.env.getTemplate(templateName).render(self._getTemplateArgs(**kwargs))
    
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

    def _addHTMLTemplate(self, templateName, **kwargs):
        self._addHTML(self.renderTemplate(templateName, **kwargs))

    def _addHTMLTemplateString(self, source, **kwargs):
        self._addHTML(
            self.env.from_string(source).render(self._getTemplateArgs(**kwargs))
        )
    
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
        ipythonDisplay(Javascript(self.renderTemplate('addScriptElements.js')))
    
    def _wrapBeforeHtml(self):
        if self.noChrome:
            return ""        
        menuTree=OrderedDict()
        for catId in ActionCategories.CAT_INFOS.keys():
            menuTree[catId]=[]    
        for handler in (handlers+systemHandlers):
            for menuInfo in handler.getMenuInfo(self.entity):
                categoryId=menuInfo.get('categoryId')
                if categoryId is not None:
                    if not categoryId in menuTree:
                        menuTree[categoryId]=[menuInfo]
                    else:
                        menuTree[categoryId].append(menuInfo) 

        return self.renderTemplate('cellOutput.html', menuTree=menuTree, numMenu=reduce(lambda n,t:n+t, [len(v) for k,v in menuTree.iteritems()], 0))
    
    def getPrefix(self, menuInfo=None):
        if ( not hasattr(self, 'prefix') ):
            self.prefix = self.options.get("prefix")
            if (self.prefix is None):
                self.prefix = str(uuid.uuid4())[:8]
        return self.prefix if menuInfo is None else (self.prefix + "-" + menuInfo['id'])
    
    def _getExecutePythonDisplayScript(self, menuInfo=None):
        return self.renderTemplate('executePythonDisplayScript.js',menuInfo=menuInfo)
        
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
            retScript+= ",prefix='" + self.getPrefix() + "'"
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
        ipythonDisplay(HTML(
            self.renderTemplate("handshake.html")
        ))
        
    def doRender(self, handlerId):
        pass
