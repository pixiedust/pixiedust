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

import warnings
from IPython.core.getipython import get_ipython
from pixiedust.utils.environment import Environment as PD_Environment

__all__ = ['addDisplayRunListener', 'display']

#Make sure that matplotlib is running inline
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    try:
        get_ipython().run_line_magic("matplotlib", "inline")
    except NameError:
        #IPython not available we must be in a spark executor
        pass

displayRunListeners = []

def addDisplayRunListener(listener):
    global displayRunListeners
    displayRunListeners.append(listener)

from .display import *
from .chart import *
if PD_Environment.hasSpark:
    from .graph import *
from .table import *
from .download import *
from .datahandler import getDataHandler
from pixiedust.utils.printEx import *
import traceback
import uuid
import pixiedust
from six import string_types

myLogger=pixiedust.getLogger(__name__ )

def display(entity, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        #todo: use ConverterRegistry
        def toPython(entity):
            from py4j.java_gateway import JavaObject
            if entity is None or not isinstance(entity, JavaObject):
                return entity

            clazz = entity.getClass().getName()
            if clazz == "org.apache.spark.sql.Dataset":
                entity = entity.toDF()
                clazz = "org.apache.spark.sql.DataFrame"

            if clazz == "org.apache.spark.sql.DataFrame":
                from pyspark.sql import DataFrame, SQLContext
                from pyspark import SparkContext
                entity = DataFrame(entity, SQLContext(SparkContext.getOrCreate(), entity.sqlContext()))

            return entity

        if 'pixiedust_display_callerText' in globals():
            callerText = globals()['pixiedust_display_callerText']
        else:
            callerText = traceback.extract_stack(limit=2)[0][3]
        if callerText is None or callerText == "":
            raise Exception("Unable to get caller text")

        pr = None
        try:
            if "cell_id" in kwargs and "showchrome" not in kwargs and "handlerId" in kwargs:
                if "gen_tests" in kwargs:
                    #remove gen_tests from command line
                    import re
                    m = re.search(",\\s*gen_tests\\s*=\\s*'((\\\\'|[^'])*)'", str(callerText), re.IGNORECASE)
                    if m is not None:
                        callerText = callerText.replace(m.group(0),"")
                    #generate new prefix
                    p = re.search(",\\s*prefix\\s*=\\s*'((\\\\'|[^'])*)'", str(callerText), re.IGNORECASE)
                    if p is not None:
                        prefix = ''.join([",prefix='", str(uuid.uuid4())[:8], "'"])
                        callerText = callerText.replace(p.group(0), prefix)
                    get_ipython().set_next_input(callerText)
                if "profile" in kwargs:
                    import cProfile
                    pr = cProfile.Profile()
                    pr.enable()

            scalaKernel = False
            if callerText is None or callerText == "" and hasattr(display, "fetchEntity"):
                callerText, entity = display.fetchEntity(entity)
                entity = toPython(entity)
                scalaKernel = True

            #get a datahandler and displayhandler for this entity
            dataHandler = getDataHandler(kwargs, entity)
            selectedHandler = getSelectedHandler(kwargs, entity, dataHandler)

            #notify listeners of a new display Run
            for displayRunListener in displayRunListeners:
                displayRunListener(entity, kwargs)
            
            #check if we have a job monitor id
            from pixiedust.utils.sparkJobProgressMonitor import progressMonitor
            if progressMonitor:
                progressMonitor.onDisplayRun(kwargs.get("cell_id"))
            
            myLogger.debug("Creating a new display handler with options {0}: {1}".format(kwargs, selectedHandler))
            try:
                displayHandler = selectedHandler.newDisplayHandler(kwargs,entity, dataHandler)
            except TypeError:
                displayHandler = selectedHandler.newDisplayHandler(kwargs, entity )
            if displayHandler is None:
                printEx("Unable to obtain handler")
                return
            
            displayHandler.handlerMetadata = selectedHandler
            displayHandler.dataHandler = dataHandler
            displayHandler.callerText = callerText
            if scalaKernel:
                displayHandler.scalaKernel = True

            if displayHandler.callerText is None:
                printEx("Unable to get entity information")
                return

            displayHandler.render()
        finally:
            if pr is not None:
                import pstats, StringIO
                pr.disable()
                s = StringIO.StringIO()
                ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
                ps.print_stats()
                myLogger.debug(s.getvalue())