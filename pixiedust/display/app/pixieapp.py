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
from six import iteritems
from abc import ABCMeta
import inspect
import sys

def route(**kw):
    def route_dec(fn):
        fn.pixiedust_route=kw
        return fn
    return route_dec

@Logger()
class PixieDustApp(Display):

    routesByClass = {}
    
    def matchRoute(self, route):
        for key,value in iteritems(route):
            #first check if the key is an field of the class
            option = getattr(self.entity, key) if self.entity is not None and hasattr(self.entity, key) else None
            #make sure we don't have a conflict with an existing function
            if callable(option):
                option = None
            if not option:
                option = self.options.get(key,None)
            if  (option is None and value=="*") or (value != "*" and option != value):
                return False
        return True
        
    def doRender(self, handlerId):
        if self.__class__.__name__ in PixieDustApp.routesByClass:
            defRoute = None
            for t in PixieDustApp.routesByClass[self.__class__.__name__]:
                if not t[0]:
                    defRoute = t[1]
                elif self.matchRoute(t[0]):
                    self.debug("match found: {}".format(t[0]))
                    getattr(self, t[1])()
                    return
            if defRoute:
                getattr(self, defRoute)()
                return

        print("Didn't find any routes for {}".format(self))

@Logger()
def PixieApp(cls):
    #reset the class routing in case the cell is being run multiple time
    clsName = "{}_{}_Display".format(inspect.getmodule(cls).__name__, cls.__name__)
    PixieDustApp.routesByClass[clsName] = []
    for name, method in iteritems(cls.__dict__):
        if hasattr(method, "pixiedust_route"):
            PixieDustApp.routesByClass[clsName].append( (method.pixiedust_route,name) )

    def __init__(self, options=None, entity=None, dataHandler=None):
        PixieDustApp.__init__(self, options or {}, entity, dataHandler)
        self.nostore_params = True

    def decoName(cls, suffix):
        return "{}_{}_{}".format(cls.__module__, cls.__name__, suffix)

    def run(self, entity=None):
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

        s = "display({})".format(var)
        try:
            sys.modules['pixiedust.display'].pixiedust_display_callerText = s
            locals()[var] = self
            return eval(s, globals(), locals())
        finally:
            del sys.modules['pixiedust.display'].pixiedust_display_callerText

    cls.run = run
        
    displayClass = type( decoName(cls, "Display"), (cls,PixieDustApp, ),{"__init__": __init__})
    
    @addId
    def getMenuInfo(self, entity, dataHandler=None):
        if entity is displayClass or entity.__class__ is displayClass:
            return [{"id": decoName(cls, "id")}]
        return []

    def newDisplayHandler(self, options, entity):
        entity.__init__(options, entity)
        return entity
    
    displayHandlerMetaClass = type( decoName(cls, "Meta"), (DisplayHandlerMeta,), {
            "getMenuInfo": getMenuInfo,
            "newDisplayHandler": newDisplayHandler
        })
    
    displayHandlerMeta = displayHandlerMetaClass()
    registerDisplayHandler( displayHandlerMeta )
    return displayClass