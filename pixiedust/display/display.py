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
from pixiedust.utils import Logger
from pixiedust.utils.template import *
import sys
import uuid
from collections import OrderedDict
import time
import re
import pixiedust
from six import iteritems, with_metaclass
from functools import reduce

myLogger = pixiedust.getLogger(__name__)

handlers=[]
systemHandlers=[]
defaultHandler=None
globalMenuInfos={}

"""
Registry of Action categories
"""
class ActionCategories(object):
    CAT_INFOS = OrderedDict([
        ("Table", {"title": "Table", "icon-class": "fa-table"}),
        ("Chart", {"title": "Chart", "icon-class": "fa-line-chart"}),
        ("Map",   {"title": "Map", "icon-class": "fa-map"}),
        ("Graph", {"title": "Graph", "icon-class": "fa-share-alt"}),
        ("Download", {"title":  "Stash dataset", "icon-class": "fa-cloud-download", "pos": 100})
    ])
    
    @staticmethod
    def sort():
        ActionCategories.CAT_INFOS = OrderedDict(sorted(iteritems(ActionCategories.CAT_INFOS), key=lambda item: item[1]["pos"] if "pos" in item[1] else 0))

def registerDisplayHandler(handlerMetadata, isDefault=False, system=False):
    global defaultHandler
    if isDefault and defaultHandler is None:
        defaultHandler=handlerMetadata
    if system:
        systemHandlers.append(handlerMetadata)
    else:
        handlers.append(handlerMetadata)

    #Add the categories
    cat = None
    for cat in handlerMetadata.createCategories():
        myLogger.debug("Adding category {0} to registry".format(str(cat)))
        if "id" not in cat:
            myLogger.error("Invalid category {0}".format(str(cat)))
        else:
            #fix the icon-path if available
            if "icon-path" in cat and ":" not in cat["icon-path"]:
                cat["icon-path"] = handlerMetadata.__module__ + ":" + cat["icon-path"]
            ActionCategories.CAT_INFOS[cat["id"]] = cat
    if cat is not None:
        #resort the registry by position
        ActionCategories.sort()
    
def getSelectedHandler(options, entity, dataHandler):
    if "cell_id" not in options:
        #No cellid, trigger handshake with the browser to get the cellId
        return CellHandshakeMeta()
        
    handlerId=options.get("handlerId")
    if handlerId is not None:
        if handlerId in globalMenuInfos:
            return globalMenuInfos[handlerId]['handler']
        else:
            #we need to find it
            for handler in (handlers+systemHandlers):
                for menuInfo in handler.getMenuInfo(entity, dataHandler):
                    if handlerId in globalMenuInfos:
                        return globalMenuInfos[handlerId]['handler']
    else:
        if defaultHandler is not None and len(defaultHandler.getMenuInfo(entity, dataHandler))>0:
            return defaultHandler
        #get the first handler that can render this object
        for handler in handlers:
            menuInfos = handler.getMenuInfo(entity, dataHandler)
            if ( menuInfos is not None and len(menuInfos)>0 ):
                return handler
    #we didn't find any, return the first
    myLogger.debug("Didn't find any handler for {0}".format(handlerId))
    return UnknownEntityMeta()

"""
misc helper functions
"""
def safeCompare(entity1, entity2):
    try:
        return entity1 == entity2
    except:
        return False

"""
PixieDust display class decorator
"""
class PixiedustDisplayMeta(object):
    def __init__(self, **kwArgs):
        self.keywordArgs = kwArgs

    def __call__(self, cls, *args, **kwargs):
        registerDisplayHandler(cls(), **self.keywordArgs)
        return cls
"""
For backward compatibility only. Deprecated
"""
class PixiedustDisplay(PixiedustDisplayMeta):
    pass

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

class DisplayHandlerMeta(with_metaclass(ABCMeta)):
    @abstractmethod
    @addId
    def getMenuInfo(self, entity, dataHandler):
        pass
    @abstractmethod
    def newDisplayHandler(self,options,entity):
        pass

    def createCategories(self):
        return []

@Logger()
class Display(with_metaclass(ABCMeta)):

    #global jinja2 Environment
    env = PixiedustTemplateEnvironment()
    
    def __init__(self, options, entity, dataHandler=None):
        self.entity=entity
        self.options=options
        self.dataHandler=dataHandler
        self.html=""
        self.scripts=list()
        self.noChrome="handlerId" in options and "showchrome" not in options
        self.addProfilingTime = False
        self.executionTime=None
        self.extraTemplateArgs={}

    def getBooleanOption(self, key, defValue):
        value = self.options.get(key, None)
        if value is None:
            return defValue
        return value == "true"

    def getDPI(self):
        return int(self.options.get("nostore_dpi", 96))

    """
        return chart height to width ration
    """
    def getHeightWidthRatio(self):
        return 0.75

    """
        return chart width scale factor
    """
    def getWidthScaleFactor(self):
        return 0.8

    def getPreferredOutputWidth(self):
        return float(self.options.get("nostore_cw", 1000)) * self.getWidthScaleFactor()

    def getPreferredOutputHeight(self):
        return float(self.getPreferredOutputWidth() * self.getHeightWidthRatio())

    def _getTemplateArgs(self, **kwargs):
        args = {
            "this":self, "entity":self.entity, "prefix":self.getPrefix(),
            "module":self.__module__
        }
        args.update(self.extraTemplateArgs)
        if kwargs:
            args.update(kwargs)
        return args

    def renderTemplate(self, templateName, **kwargs):
        return self.env.getTemplate(templateName).render(self._getTemplateArgs(**kwargs))
    
    def render(self):
        handlerId=self.options.get("handlerId")
        if handlerId is None or not self.noChrome:
            #get the first menuInfo for this handler and generate a js call
            menuInfo = globalMenuInfos[handlerId] if handlerId is not None and handlerId in globalMenuInfos else None
            if menuInfo is None:
                menuInfos = self.handlerMetadata.getMenuInfo(self.entity, self.dataHandler)
                if len(menuInfos)>0:
                    menuInfo = menuInfos[0]
            if menuInfo is not None:
                self._addHTML("""
                    <script>
                    ({0})();
                    </script>
                """.format(self._getExecutePythonDisplayScript(menuInfo)))
        else:
            start = time.clock()
            self.doRender(handlerId)
            self.executionTime = time.clock() - start
            
        #check if pixiedust object is already installed on the client
        #Experimental, not ready for prime time yet
        #if self.options.get("nostore_pixiedust", "false") != "true":
        #    js = self.renderTemplate( "addScriptCode.js", code = self.renderTemplate("pixiedust.js") )
        #    self.debug("pixiedust code: {}".format(js))
        #    ipythonDisplay(Javascript(js))

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

    def _addJavascript(self, javascript):
        ipythonDisplay( Javascript(javascript) )

    def _addJavascriptTemplate(self, templateName, **kwargs):
        self._addJavascript(self.renderTemplate(templateName, **kwargs))
    
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
            for menuInfo in handler.getMenuInfo(self.entity, self.dataHandler):
                #fix the icon-path if available
                if "icon-path" in menuInfo and ":" not in menuInfo["icon-path"]:
                    menuInfo["icon-path"] = handler.__module__ + ":" + menuInfo["icon-path"]
                categoryId=menuInfo.get('categoryId')
                if categoryId is not None:
                    if not categoryId in menuTree:
                        menuTree[categoryId]=[menuInfo]
                    else:
                        menuTree[categoryId].append(menuInfo)
        return self.renderTemplate('cellOutput.html', menuTree=menuTree, numMenu=reduce(lambda n,t:n+t, [len(v) for k,v in iteritems(menuTree)], 0))
    
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
        def updateCommand(command,key,value):
            hasValue = value is not None and value != ''
            replaceValue = (key+"=" + str(value)) if hasValue else ""
            pattern = ("" if hasValue else ",")+"\\s*" + key + "\\s*=\\s*'((\\\\'|[^'])*)'"
            m = re.search(pattern, str(command), re.IGNORECASE)
            retCommand = command
            if m is not None:
                retCommand = command.replace(m.group(0), key+"='"+value+"'" if hasValue else "");
            elif hasValue:
                k=command.rfind(")")
                retCommand = command[:k]
                retCommand+=","+key+"='"+value+"'"
                retCommand+= command[k:]
            return retCommand

        command = self.callerText
        if command is None:
            raise ValueError("command is None")
        if menuInfo:
            command = updateCommand(command, "handlerId", menuInfo['id'])
            command = updateCommand(command, "prefix", self.getPrefix())
        if "cell_id" not in self.options:
            command = updateCommand(command, "cell_id", 'cellId')
        for key,value in iteritems(addOptionDict):
            command = updateCommand(command, key, value)

        command = updateCommand(command, "showchrome", None)
        #remove showchrome if there
        return command.replace("\"","\\\"")

    def getCategory(self, catId):
        if catId in ActionCategories.CAT_INFOS:
            return ActionCategories.CAT_INFOS[catId]
        myLogger.error("catId {0} not found in Registry".format(catId))
        
    def getCategoryTitle(self,catId):
        if catId in ActionCategories.CAT_INFOS:
            return ActionCategories.CAT_INFOS[catId]['title']
        elif catId == "Download":
            return "Stash dataset"
        myLogger.error("catId {0} not found in Registry".format(catId))
        return ""
            
    def getCategoryIconClass(self,catId):
        if catId in ActionCategories.CAT_INFOS:
            return ActionCategories.CAT_INFOS[catId]['icon-class']
        elif catId == "Download":
            return "fa-cloud-download"
        myLogger.error("catId {0} not found in Registry".format(catId))
        return ""
        
    def _wrapAfterHtml(self):
        if ( self.noChrome ):
            return ("""<div class="executionTime" id="execution{0}">Execution time: {1}s</div>""".format(self.getPrefix(), str(self.executionTime))) if self.executionTime is not None and self.addProfilingTime else ""
        return "</div>"

#Special handler for fetching the id of the cell being executed 
class CellHandshakeMeta(DisplayHandlerMeta):
    def getMenuInfo(self,entity, dataHandler):
       return []
    def newDisplayHandler(self,options,entity):
        return CellHandshake(options,entity)
        
class CellHandshake(Display):
    snifferCallbacks = []
    @staticmethod
    def addCallbackSniffer(sniffer):
        CellHandshake.snifferCallbacks.append(sniffer)
    def render(self):
        ipythonDisplay(HTML(
            self.renderTemplate("handshake.html")
        ))
        
    def doRender(self, handlerId):
        pass

#Special handler used when no handlers was found to process the entity 
class UnknownEntityMeta(DisplayHandlerMeta):
    def getMenuInfo(self,entity, dataHandler):
       return []
    def newDisplayHandler(self,options,entity):
        return UnknownEntityDisplay(options,entity)
        
class UnknownEntityDisplay(Display):
    def render(self):
        ipythonDisplay(HTML(
            self.renderTemplate("unknownEntity.html")
        ))
        
    def doRender(self, handlerId):
        pass
