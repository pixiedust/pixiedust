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
from pixiedust.display import display
from pixiedust.display.display import *
from pixiedust.utils.shellAccess import ShellAccess
from pixiedust.utils import Logger
from six import iteritems, string_types
from collections import OrderedDict
import inspect
import sys
from six import string_types

def route(**kw):
    def route_dec(fn):
        fn.pixiedust_route=kw
        return fn
    return route_dec

#Global object enables system wide customization of PixieApp run option
pixieAppRunCustomizer = None

def runPixieApp(app, parentApp=None, entity=None, **kwargs):
    if isinstance(app, PixieDustApp):
        app.run(entity, **kwargs)
    elif isinstance(app, string_types):
        parts = app.split('.')
        getattr(__import__('.'.join(parts[:-1]), None, None, [parts[-1]], 0), parts[-1])().run(entity, **kwargs)
    else:
        raise ValueError("Invalid argument to runPixieApp. Only PixieApp or String allowed")

@Logger()
class PixieDustApp(Display):

    routesByClass = {}

    def getOptionValue(self, optionName):
        #first check if the key is an field of the class
        option = getattr(self.entity, optionName) if self.entity is not None and hasattr(self.entity, optionName) else None
        #make sure we don't have a conflict with an existing function
        if callable(option):
            option = None
        if option is None:
            option = self.options.get(optionName, None)
        return option

    def matchRoute(self, route):
        for key,value in iteritems(route):
            option = self.getOptionValue(key)
            if  (option is None and value=="*") or (value != "*" and option != value):
                return False
        return True

    def injectArgs(self, method, route):
        argspec = inspect.getargspec(method)
        args = argspec.args
        args = args[1:] if hasattr(method, "__self__") else args
        return OrderedDict(zip([a for a in args],[ self.getOptionValue(arg) for arg in args] ) )

    def doRender(self, handlerId):
        if self.__class__.__name__ in PixieDustApp.routesByClass:
            defRoute = None
            retValue = None
            injectedArgs = {}
            try:
                dispatchKey = "widgets" if "widget" in self.options else "routes"
                for t in PixieDustApp.routesByClass[self.__class__.__name__][dispatchKey]:
                    if not t[0]:
                        defRoute = t[1]
                    elif self.matchRoute(t[0]):
                        self.debug("match found: {}".format(t[0]))
                        meth = getattr(self, t[1])
                        injectedArgs = self.injectArgs(meth, t[0])
                        self.debug("Injected args: {}".format(injectedArgs))
                        retValue = meth(*list(injectedArgs.values()))
                        return
                if defRoute:
                    retValue = getattr(self, defRoute)()
                    return
            finally:
                if isinstance(retValue, string_types):
                    self._addHTMLTemplateString(retValue, **injectedArgs )
                elif isinstance(retValue, dict):
                    body = self.renderTemplateString(retValue.get("body", ""))
                    jsOnLoad = self.renderTemplateString(retValue.get("jsOnLoad", ""))
                    jsOK = self.renderTemplateString(retValue.get("jsOK", ""))
                    dialogRoot = retValue.get("dialogRoot", None)
                    if dialogRoot is not None:
                        jsOnLoad = """pixiedust.dialogRoot="{}";\n{}""".format(self.renderTemplateString(dialogRoot), jsOnLoad)
                    if body is not None:
                        self._addHTMLTemplateString("""
                        {{body}}
                        <pd_dialog>
                            <pd_onload>{{jsOnLoad|htmlAttribute}}</pd_onload>
                            <pd_ok>{{jsOK|htmlAttribute}}</pd_ok>
                        </pd_dialog>
                        """, body=body, jsOnLoad=jsOnLoad, jsOK=jsOK)

        print("Didn't find any routes for {}".format(self))

    def getDialogOptions(self):
        return {}

@Logger()
def PixieApp(cls):
    #reset the class routing in case the cell is being run multiple time
    clsName = "{}_{}_Display".format(inspect.getmodule(cls).__name__, cls.__name__)
    PixieDustApp.routesByClass[clsName] = {"routes":[], "widgets":[]}
    #put the routes that define a widget in a separate bucket

    def walk(cl):
        for name, method in iteritems(cl.__dict__):
            if hasattr(method, "pixiedust_route"):
                if "widget" in method.pixiedust_route:
                    PixieDustApp.routesByClass[clsName]["widgets"].append( (method.pixiedust_route,name) )
                else:
                    PixieDustApp.routesByClass[clsName]["routes"].append( (method.pixiedust_route,name) )
        for c in [c for c in cl.__bases__]:
            walk(c)
    walk(cls)

    #re-order the routes according to the number of constraints e.g. from more to less specific
    p = PixieDustApp.routesByClass[clsName]["routes"]
    PixieDustApp.routesByClass[clsName]["routes"] = [p[a[1]] for a in sorted([(len(a[0]), i) for i,a in enumerate(p)], reverse=True)]

    def __init__(self, options=None, entity=None, dataHandler=None):
        PixieDustApp.__init__(self, options or {}, entity, dataHandler)
        if not hasattr(self, "pd_initialized"):
            if hasattr(self, "setup"):
                self.setup()
            self.nostore_params = True
            self.pd_initialized = True

    def getPixieAppEntity(self):
        return self.pixieapp_entity if hasattr(self, "pixieapp_entity") else None

    def formatOptions(self,options):
        """Helper method that convert pd options from Json format to pixieApp html attribute compliant format"""
        return ';'.join(["{}={}".format(key,value) for (key, value) in iteritems(options)])

    def decoName(cls, suffix):
        return "{}_{}_{}".format(cls.__module__, cls.__name__, suffix)

    def run(self, entity=None, **kwargs):
        for key,value in iteritems(kwargs):
            setattr(self, key, value)
        if entity is not None:
            self.pixieapp_entity = entity
        var = None
        for key in ShellAccess:
            if ShellAccess[key] is self:
                var = key

        if not var:
            #If we're here, the user must have created the instance inline, assign a variable dynamically
            var = cls.__name__ + "_instance"
            ShellAccess[var] = self

        self.runInDialog = kwargs.get("runInDialog", "false") is "true"
        options = {"nostore_pixieapp": var, "nostore_ispix":"true", "runInDialog": "true" if self.runInDialog else "false"}
        if self.runInDialog:
            options.update(self.getDialogOptions())

        options.update({'handlerId': decoName(cls, "id")})
        if "options" in kwargs and isinstance(kwargs['options'], dict):
            options.update(kwargs['options'])
        if pixieAppRunCustomizer is not None and callable(getattr(pixieAppRunCustomizer, "customizeOptions", None)):
            pixieAppRunCustomizer.customizeOptions(options)

        opts = [(k, str(v).lower() if isinstance(v, bool) else v) for (k,v) in iteritems(options) if v is not None]
        s = "display({}{})".format(var, reduce(lambda k,v: k + "," + v[0] + "='" + str(v[1]) + "'", opts, ""))
        try:
            sys.modules['pixiedust.display'].pixiedust_display_callerText = s
            locals()[var] = self
            return eval(s, globals(), locals())
        finally:
            del sys.modules['pixiedust.display'].pixiedust_display_callerText
        
    displayClass = type( decoName(cls, "Display"), (cls,PixieDustApp, ),{
        "__init__": __init__, 
        "run": run, 
        "getPixieAppEntity":getPixieAppEntity
    })
    ShellAccess["newDisplayClass"] = displayClass

    def prettyFormat(o):
        return "{} at {}".format(o, id(o))
    
    @addId
    def getMenuInfo(self, entity, dataHandler=None):
        if entity is displayClass or entity.__class__ is displayClass:
            return [{"id": decoName(cls, "id")}]
        return []

    def newDisplayHandler(self, options, entity):
        if entity is displayClass or entity.__class__ is displayClass:
            entity.__init__(options, entity)
            return entity
        elif options.get("nostore_pixieapp") is not None:
            from pixiedust.utils.shellAccess import ShellAccess
            papp = ShellAccess[options.get("nostore_pixieapp")]
            if papp is not None and hasattr(papp, "newDisplayHandler"):
                fn = papp.newDisplayHandler
                if callable(fn):
                    return fn(options, entity)
        return None

    displayHandlerMetaClass = type( decoName(cls, "Meta"), (DisplayHandlerMeta,), {
            "getMenuInfo": getMenuInfo,
            "newDisplayHandler": newDisplayHandler
        })

    displayHandlerMeta = displayHandlerMetaClass()
    ShellAccess["displayHandlerMeta"] = displayHandlerMeta
    registerDisplayHandler( displayHandlerMeta )
    return displayClass
