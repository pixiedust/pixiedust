# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2018
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

from abc import ABCMeta, abstractmethod
from IPython.display import display as ipythonDisplay, HTML, Javascript
from pixiedust.utils import Logger
from pixiedust.utils.astParse import parse_function_call
from pixiedust.utils.template import *
import sys
import uuid
from collections import OrderedDict
import time
import re
import six
import pixiedust
from six import iteritems, with_metaclass, string_types, text_type
from functools import reduce
import json

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
    listHandlers = systemHandlers if system else handlers
    found = False
    def myeq(a,b):
        return a.__class__.__module__ == b.__class__.__module__ and a.__class__.__name__ == b.__class__.__name__
    for i,h in enumerate(listHandlers):
        if (not found and myeq(h, handlerMetadata)):
            #duplicate found, happens mostly when user is iterating on the notebook
            for x in [ x for x in globalMenuInfos if myeq(globalMenuInfos[x]['handler'], handlerMetadata)]:
                del(globalMenuInfos[x])
            listHandlers[i] = handlerMetadata
            found = True

    if not found:
        listHandlers.append(handlerMetadata)

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
    elif options.get('runInDialog', 'false') == 'true':
        #we are running in a dialog
        return RunInDialogMeta()
        
    handlerId=options.get("handlerId")
    if handlerId is not None:
        if handlerId in globalMenuInfos:
            return globalMenuInfos[handlerId]['handler']
        else:
            #we need to find it
            def findHandlerId(e):
                for handler in (handlers+systemHandlers):
                    for menuInfo in handler.getMenuInfo(e, dataHandler):
                        if handlerId in globalMenuInfos:
                            return globalMenuInfos[handlerId]['handler']

            retValue = findHandlerId(entity)            
            if retValue:
                return retValue

    #If we're here, then either no handlerId was specified or if it was, it was not found
    if handlerId is not None:
        myLogger.debug("Unable to resolve handlerId {} for entity {}. Trying to find a suitable one".format(handlerId, entity) )

    if defaultHandler is not None and len(defaultHandler.getMenuInfo(entity, dataHandler))>0:
        return defaultHandler
    #get the first handler that can render this object
    for handler in handlers:
        menuInfos = handler.getMenuInfo(entity, dataHandler)
        if ( menuInfos is not None and len(menuInfos)>0 ):
            #set the handlerId in the options
            options["handlerId"] = menuInfos[0].get("id")
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
        self.delaySaving = False    #tell the front-end runtime to delay the output saving to give the renderer time to process

    @property
    def isStreaming(self):
        return self.dataHandler.isStreaming if self.dataHandler is not None else False

    @property
    def is_running_on_dsx(self):
        return pixiedust.utils.environment.Environment.isRunningOnDSX
    
    @property
    def is_PY3(self):
        return six.PY3

    def getBooleanOption(self, key, defValue):
        value = self.options.get(key, None)
        if value is None:
            return defValue
        return value == "true"

    @property
    def is_gateway(self):
        return "gateway" in self.options

    def get_options_dialog_pixieapp(self):
        """
        Return the fully qualified path to a PixieApp used to display the dialog options
        PixieApp must inherit from pixiedust.display.chart.options.baseOptions.BaseOptions
        """
        return "pixiedust.display.chart.options.defaultOptions.DefaultOptions"

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
        return 0.8 if "no_margin" not in self.options else 1.0

    def getPreferredOutputWidth(self):
        sizeratio = float(self.options.get('chartsize', 100)) / 100
        return float(self.options.get("nostore_cw", 1000)) * sizeratio * self.getWidthScaleFactor()

    def getPreferredOutputHeight(self):
        ch = self.options.get("nostore_ch", None)
        vh = self.options.get("nostore_vh", None) # viewport height
        cappedheight = 500 if vh is None else max(500, float(vh) * 0.5) # capped max height
        if ch is not None:
            return float(ch)
        else:
            return min(cappedheight, float(self.getPreferredOutputWidth() * self.getHeightWidthRatio()))

    def get_pd_controls(self, **kwargs):
        menuInfo = kwargs.pop("menuInfo", None)
        black_list = kwargs.pop("black_list", [])
        command = kwargs.pop("command", self._genDisplayScript(menuInfo=menuInfo))
        parsed_command = parse_function_call(command)
        controls = {
            "prefix": kwargs.pop("prefix", self.getPrefix()),
            "command": "{}({},{})".format(
                parsed_command['func'],
                ",".join(parsed_command['args']),
                ",".join( ["{}='{}'".format(k,v) for k,v in iteritems(parsed_command['kwargs']) if k not in black_list])
            ),
            "entity": parsed_command['args'][0],
            "options": parsed_command['kwargs'],
            "sniffers": [cb() for cb in CellHandshake.snifferCallbacks],
            "avoidMetadata": menuInfo is not None,
            "include_keys": ['filter']
        }
        for key,value in iteritems(kwargs):
            if key in controls and isinstance(controls[key], dict) and isinstance(value, dict):
                controls[key].update(value)
            else:
                controls[key] = value

        for key in black_list:
            controls["options"].pop(key, None)
        return controls

    def _getTemplateArgs(self, **kwargs):
        args = {
            "this": self, 
            "entity": self.entity, 
            "prefix": self.getPrefix(),
            "module": self.__module__,
            "gateway": self.options.get("gateway", None),
            "pd_controls": json.dumps(
                self.get_pd_controls(
                    menuInfo=kwargs.get("menuInfo", None)
                )
            )
        }

        args.update(self.extraTemplateArgs)
        if kwargs:
            args.update(kwargs)
        return args

    def renderTemplate(self, templateName, **kwargs):
        return self.env.getTemplate(templateName).render(self._getTemplateArgs(**kwargs))

    """
        check if pixiedust object is already installed on the client
    """
    def _checkPixieDustJS(self):
        if self.delaySaving:
            self.options["nostore_delaysave"] = "true"
        if self.options.get("nostore_pixiedust", "false") != "true":
            self.options["nostore_pixiedust"] = "true"
            ipythonDisplay(Javascript(self.renderTemplate( "addScriptCode.js", type="css", code = self.renderTemplate("pixiedust.css") )))
            js = self.renderTemplate( "addScriptCode.js", type="javascript", code = self.renderTemplate("pixiedust.js") )
            #self.debug("pixiedust code: {}".format(js))
            ipythonDisplay(Javascript(js))
    
    def render(self):
        self._checkPixieDustJS()
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

    def renderTemplateString(self, source, **kwargs):
        return self.env.from_string(source).render(self._getTemplateArgs(**kwargs))

    def _addHTMLTemplateString(self, source, **kwargs):
        self._addHTML(
            self.renderTemplateString(source, **kwargs)
        )

    def _addJavascript(self, javascript):
        ipythonDisplay( Javascript(javascript) )

    def _addJavascriptTemplate(self, templateName, **kwargs):
        self._addJavascript(self.renderTemplate(templateName, **kwargs))
    
    def _safeString(self, s):
        if not isinstance(s, string_types):
            return str(s)
        else:
            return text_type(s.encode('ascii', 'ignore'), 'ascii')
        
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
        return self.renderTemplateString("""
            {% set targetId=divId if divId and divId.startswith("$") else ("'"+divId+"'") if divId else "'wrapperHTML" + prefix + "'" %}
            function(){
                pixiedust.executeDisplay(
                    {{pd_controls}},
                    {'targetDivId': {{targetId}} }
                );
            }
            """, menuInfo=menuInfo)
        
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

        command = self.callerText if hasattr(self, "callerText") else None
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

        for opt in ["nostore_pixiedust", "nostore_delaysave"]:
            if opt in self.options:
                command = updateCommand(command, opt, self.options[opt])
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

@Logger()    
class CellHandshake(Display):
    snifferCallbacks = []

    def __init__(self, options, entity):
        Display.__init__(self, options, entity)
        self.nostore_params = True

    @staticmethod
    def addCallbackSniffer(sniffer):
        CellHandshake.snifferCallbacks.append(sniffer)
    def render(self):
        self._checkPixieDustJS()
        ipythonDisplay(HTML(
            self.renderTemplate(
                "handshake.html", 
                org_params = ','.join(list(self.options.keys())),
                pixiedust_js = self.renderTemplate("pixiedust.js")
            )
        ))
        
    def doRender(self, handlerId):
        pass

#Special handler for running in a dialog
class RunInDialogMeta(DisplayHandlerMeta):
    def getMenuInfo(self, entity, dataHandler):
        return []
    def newDisplayHandler(self, options, entity):
        return RunInDialog(options, entity)

@Logger()
class RunInDialog(Display):
    def render(self):
        self._checkPixieDustJS()
        self.debug("In RunInDialog")
        # del self.options['runInDialog']
        ipythonDisplay(Javascript("pixiedust.executeInDialog({0},{1});".format(
            json.dumps(
                self.get_pd_controls(
                    prefix = self.options.get("prefix", self.getPrefix()),
                    black_list = ['runInDialog']
                )
            ),
            json.dumps({
                "nostoreMedatadata": True,
                "options":{
                    "runInDialog": ""
                }
            })
        )))
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
        ipythonDisplay(self.entity)
        
    def doRender(self, handlerId):
        pass
