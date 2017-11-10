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

from ..display import ChartDisplay
from abc import abstractmethod, ABCMeta
import traceback
import pixiedust
from collections import OrderedDict
from six import PY2, with_metaclass,iteritems
from pixiedust.display import addDisplayRunListener
from pixiedust.display.chart.renderers import PixiedustRenderer
from pixiedust.utils import cache,Logger
from pixiedust.utils.shellAccess import ShellAccess
from .commonOptions import commonOptions as co
import pandas as pd
import time
import inspect
import re

class ShowChartOptionDialog(Exception):
    pass

class WorkingDataCache(with_metaclass( 
        type("",(type,),{
            "workingDataCache":{},
            "__getitem__":lambda cls, key: cls.workingDataCache.get(key),
            "__setitem__":lambda cls, key,val: cls.workingDataCache.update({key:val}),
            "__getattr__":lambda cls, key: cls.workingDataCache.get(key),
            "__setattr__":lambda cls, key, val: cls.workingDataCache.update({key:val})
        }), object
    )):

    myLogger = pixiedust.getLogger(__name__)

    @staticmethod
    def onNewDisplayRun(entity, options):
        if "cell_id" in options and "showchrome" in options:
            #User is doing a new display run from the cell, clear the cache as we don't know if the entity has changed
            WorkingDataCache.removeEntry(options["cell_id"])

    @staticmethod
    def removeEntry(key):
        WorkingDataCache.workingDataCache.pop(key, None)

    @staticmethod
    def putInCache(options, data, constraints):
        if "cell_id" not in options or "noChartCache" in options:
            return
        constraints.pop("self",None)
        WorkingDataCache[options["cell_id"]] = {
            "data": data,
            "constraints": constraints
        }

    @staticmethod
    def getFromCache(options, constraints ):
        if "cell_id" not in options:
            return None
        constraints.pop("self",None)
        cellId = options["cell_id"]
        value = WorkingDataCache[cellId]
        if value:
            WorkingDataCache.myLogger.debug("Found cache data for {}. Validating integrity...".format(cellId))
            for item in list(value["constraints"].items()):
                if item[0] not in constraints or item[1] != constraints[item[0]]:
                    WorkingDataCache.myLogger.debug("Cache data not validated for key {0}. Expected Value is {1}. Got {2}. Destroying it!...".format(item[0], item[1], constraints[item[0]]))
                    WorkingDataCache.removeEntry(cellId)
                    return None
            WorkingDataCache.myLogger.debug("Cache data validated for {}. Using it!...".format(cellId))
            return value["data"]
        WorkingDataCache.myLogger.debug("No Cache Entry found for {}".format(cellId))

#add a display Run Listener 
addDisplayRunListener( lambda entity, options: WorkingDataCache.onNewDisplayRun(entity, options) )

#common Chart Options injection decorator
def commonChartOptions(func):
    def wrapper(cls, *args, **kwargs):
        commonOptions = []
        if hasattr(cls, "handlerId") and hasattr(cls, 'commonOptions'):
            handler = cls.commonOptions.get(cls.handlerId, [])
            if callable(handler):
                handler = handler(cls)
            commonOptions += handler
            fctSet = set()
            for cl in reversed(inspect.getmro(cls.__class__)):
                if hasattr(cl, func.__name__):
                    f = getattr(cl, func.__name__)
                    if f not in fctSet:
                        fctSet.add(f)
                        if hasattr(f, "func"):
                            f = f.func
                        opts = f(cls, *args, **kwargs)
                        commonOptions += opts
            return commonOptions
        return commonOptions + func(cls, *args, **kwargs )
    wrapper.func = func
    return wrapper

@Logger()
class BaseChartDisplay(with_metaclass(ABCMeta, ChartDisplay)):

    commonOptions = co

    def __init__(self, options, entity, dataHandler=None):
        super(BaseChartDisplay,self).__init__(options,entity,dataHandler)
        #note: since this class can be subclassed from other module, we need to mark the correct resource module with resModule so there is no mixup
        self.extraTemplateArgs["resModule"]=BaseChartDisplay.__module__
        self.messages = []

    """
        Subclass can override: return an array of option metadata
    """
    @commonChartOptions
    def getChartOptions(self):
        return []

    def validateOptions(self):
        #start with the value Field, if empty, then we need to add a dummy column
        value_fields = self.getValueFields()
        if self.supportsKeyFields(self.handlerId) and len(value_fields) == 0:
            new_col_name = self.dataHandler.add_numerical_column()
            self.valueFields = [new_col_name]
            self.aggregation = "COUNT"
        #validate options
        chartOptions = self.getChartOptions()   
        self.debug("chartOptions {}".format(chartOptions)) 
        ord = OrderedDict([(o["name"],o["validate"]) for o in chartOptions if "validate" in o and "name" in o])
        remKeys = []
        for key,value in iteritems(self.options):
            if key in ord:
                values = value.split(",")
                self.debug("values: {0}".format(values))
                for v in values:
                    self.debug("Calling with {0}".format(v))
                    passed, message = ord.get(key)(v)
                    if not passed:
                        self.addMessage("Filtered option {0} with value {1}. Reason {2}".format(key, value, message))
                        remKeys.append(key)
                        break

        for key in remKeys:
            del self.options[key]

    def getExtraFields(self):
        return []

    def addMessage(self, message):
        self.messages.append(message)

    @cache(fieldName="workingPandasDataFrame")
    def getWorkingPandasDataFrame(self):
        xFields = self.getKeyFields()
        yFields = self.getValueFields()
        extraFields = self.getExtraFields()
        aggregation = self.getAggregation()
        maxRows = self.getMaxRows()
        timeseries = self.options.get("timeseries", 'false')
        #remember the constraints for this cache, they are the list of variables
        constraints = locals()

        workingDF = WorkingDataCache.getFromCache(self.options, constraints )
        if workingDF is None:
            workingDF = self.dataHandler.getWorkingPandasDataFrame(xFields, yFields, extraFields = extraFields, aggregation=aggregation, maxRows = maxRows )
            WorkingDataCache.putInCache(self.options, workingDF, constraints)
        
        if self.options.get("sortby", None):
            sortby = self.options.get("sortby", None)
            if sortby == 'Keys ASC':
                workingDF = workingDF.sort_values(xFields, ascending=True)
            elif sortby == 'Keys DESC':
                workingDF = workingDF.sort_values(xFields, ascending=False)
            elif sortby == 'Values ASC':
                workingDF = workingDF.sort_values(yFields, ascending=True)
            elif sortby == 'Values DESC':
                workingDF = workingDF.sort_values(yFields, ascending=False)

        if self.options.get("debug", None):
            self.debug("getWorkingPandasDataFrame returns: {0}".format(workingDF) )
            ShellAccess["workingPDF"] = workingDF    
        return workingDF

    def getWorkingDataSlice1( self, col, sort = False ):
        colData = self.getWorkingPandasDataFrame()[col].values.tolist()
        if sort:
            return sorted(colData)
        else:
            return colData

    def getWorkingDataSlice( self, col1, col2, sort = False ):
        col1Data = self.getWorkingPandasDataFrame()[col1].values.tolist()
        col2Data = self.getWorkingPandasDataFrame()[col2].values.tolist()
        if sort:
            return zip(*sorted(zip(col1Data, col2Data )))
        else:
            return [col1Data, col2Data]

    @cache(fieldName="maxRows")
    def getMaxRows(self):
        return int(self.options.get("rowCount","100"))

    #helper method
    def _getField(self, fieldName):
        if not hasattr(self, fieldName):
            return None
        return getattr(self, fieldName)

    def getChartContext(self, handlerId):
        return None

    def getChartErrorDialogBody(self, handlerId, dialogTemplate, dialogOptions):
        return self.renderTemplate(dialogTemplate, **dialogOptions)

    @abstractmethod
    def doRenderChart(self):
        pass

    def isMap(self, handlerId):
        return False

    def supportsKeyFields(self, handlerId):
        return True

    def supportsKeyFieldLabels(self, handlerId):
        return True

    def supportsLegend(self, handlerId):
        return True

    def supportsAggregation(self, handlerId):
        return True

    def getDefaultAggregation(self, handlerId):
        return "SUM"

    def getPreferredDefaultKeyFieldCount(self, handlerId):
        return 1

    @cache(fieldName="keyFields")
    def getKeyFields(self):
        """ Get the dataframe field names from metadata (usually specified by the user 
        as key fields in the chart option dialog)

        Args: 
            self (class): class that extends BaseChartDisplay

        Returns: 
            List of strings: dataframe field names

        Raises:
            Calls ShowChartOptionDialog() if array is empty
        """
        fieldNames = self.getFieldNames() # get all field names in data format-independent way
        if len(fieldNames) == 0:
            return []
        if self.supportsKeyFields(self.handlerId) == False:
            return []
        keyFields = []
        keyFieldStr = self.options.get("keyFields")
        if keyFieldStr is not None:
            keyFields = keyFieldStr.split(",")
            keyFields = [val for val in keyFields if val in fieldNames]
        if len(keyFields) == 0:
            raise ShowChartOptionDialog()
        else:
            return keyFields

    @cache(fieldName="keyFieldLabels")
    def getKeyFieldLabels(self):
        k = self.getKeyFields()
        if (len(k) == 0):
            return []
        return self.getWorkingPandasDataFrame().groupby(k).groups.keys()

    def getPreferredDefaultValueFieldCount(self, handlerId):
        return 2

    @cache(fieldName="valueFields")   
    def getValueFields(self):
        fieldNames = self.getFieldNames()
        if len(fieldNames) == 0:
            return []
        aggregation = self.getAggregation()
        valueFields = []
        valueFieldStr = self.options.get("valueFields")
        if valueFieldStr is not None:
            valueFields = valueFieldStr.split(",")
            valueFields = [val for val in valueFields if val in fieldNames]
        numericValueFields = []
        for valueField in valueFields:
            if self.dataHandler.isNumericField(valueField) or aggregation == "COUNT":
                numericValueFields.append(valueField)

        if not self.supportsKeyFields(self.handlerId) and len(numericValueFields) == 0:
            raise ShowChartOptionDialog()
        return numericValueFields
    
    def canRenderChart(self):
        aggregation = self.getAggregation()
        if (aggregation == "COUNT"):
            return (True, None)
        else:
            for field in self.dataHandler.schema.fields:
                if self.dataHandler.isNumericType(field):
                    return (True, None)
            return (False, "At least one numerical column required.")

    def getDialogInfo(self, handlerId):
        context = self.getChartContext(handlerId)
        dialogOptions = { "fieldNames":self.getFieldNames(True),\
            "fieldNamesAndTypes":self.getFieldNamesAndTypes(True, True),\
            "keyFieldsSupported":self.supportsKeyFields(handlerId),\
            "legendSupported":self.supportsLegend(handlerId),\
            "aggregationSupported":self.supportsAggregation(handlerId),\
            "aggregationOptions":["SUM","AVG","MIN","MAX","COUNT"]\
        }
        if (context is not None):
            dialogTemplate = context[0]
            dialogOptions.update(context[1])
        else:
            dialogTemplate = BaseChartDisplay.__module__ + ":baseChartOptionsDialogBody.html"

        return (dialogTemplate, dialogOptions)

    def getRendererList(self):
        return PixiedustRenderer.getRendererList(self.options, self.entity, self.isStreaming)

    @cache(fieldName="aggregation")
    def getAggregation(self):
        if not self.supportsAggregation(self.handlerId):
            return None
        # get aggregation value (set to default if it doesn't exist)
        aggregation = self.options.get("aggregation")
        if aggregation is None:
            aggregation = self.getDefaultAggregation(self.handlerId)
            self.options["aggregation"] = aggregation
        return aggregation

    @cache(fieldName="fieldNames")
    def getFieldNames(self, expandNested=True):
        return self.dataHandler.getFieldNames(expandNested)

    @cache(fieldName="fieldNamesAndTypes")
    def getFieldNamesAndTypes(self, expandNested=True, sorted=False):
        fieldNames = self.getFieldNames(True)
        fieldNamesAndTypes = []
        for fieldName in fieldNames:
            fieldType = "unknown/unsupported"
            if self.dataHandler.isNumericField(fieldName):
                fieldType = "numeric"
            elif self.dataHandler.isDateField(fieldName):
                fieldType = "date/time"
            elif self.dataHandler.isStringField(fieldName):
                fieldType = "string"
            fieldNamesAndTypes.append((fieldName, fieldType))
        if sorted:
            fieldNamesAndTypes.sort(key=lambda x: x[0])
        return fieldNamesAndTypes

    def doRender(self, handlerId):
        self.handlerId = handlerId
        optionsTitle = self.camelCaseSplit(handlerId, True) + " Options"

        # field names
        fieldNames = self.getFieldNames(True)
        (dialogTemplate, dialogOptions) = self.getDialogInfo(handlerId)

        # go
        try:
            self.validateOptions()

            if self.options.get("debug", None):
                self.logStuff()
            keyFields = self.getKeyFields()
            valueFields = self.getValueFields()
        except ShowChartOptionDialog:
            self.dialogBody = self.renderTemplate(dialogTemplate, **dialogOptions)
            self._addJavascriptTemplate("chartOptions.dialog", optionsDialogBody=self.dialogBody, 
                optionsTitle=optionsTitle, inScript=True, **dialogOptions)
            return
        
        # render
        try:
            self.dialogBody = self.renderTemplate(dialogTemplate, **dialogOptions)

            # validate if we can render
            canRender, errorMessage = self.canRenderChart()
            if canRender == False:
                raise Exception(errorMessage)

            # set the keyFields and valueFields options if this is the first time
            # do this after call to canRenderChart as some charts may need to know that they have not been set
            setKeyFields = self.options.get("keyFields") is None
            setValueFields = self.options.get("valueFields") is None
            if setKeyFields and len(keyFields) > 0:
                self.options["keyFields"] = ",".join(keyFields)
            if setValueFields and len(valueFields) > 0:
                self.options["valueFields"] = ",".join(valueFields)        

            chartFigure = self.doRenderChart()
            if self.options.get("debugFigure", None):
                self.debug(chartFigure)
            if self.options.get("nostore_figureOnly", None):
                self._addHTML(chartFigure)
            else:
                self._addHTMLTemplate("renderer.html", chartFigure=chartFigure, optionsDialogBody=self.dialogBody, 
                    optionsTitle=optionsTitle, **dialogOptions)
        except Exception as e:
            self.exception("Unexpected error while trying to render BaseChartDisplay")
            errorHTML = """
                <div style="min-height: 50px;">
                    <div style="color: red;position: absolute;bottom: 0;left: 0;">{0}</div>
                </div>
            """.format(str(e))
            if self.options.get("nostore_figureOnly", None):
                self._addHTML(errorHTML)
            else:
                self._addHTMLTemplate("renderer.html", chartFigure=errorHTML, optionsDialogBody=self.dialogBody, 
                    optionsTitle=optionsTitle, **dialogOptions)

    def logStuff(self):
        try:
            self.debug("Key Fields: {0}".format(self.getKeyFields()) )
            ShellAccess['keyFields'] = self.getKeyFields()
            self.debug("Key Fields Labels: {0}".format(self.getKeyFieldLabels()))
            self.debug("Value Fields: {0}".format(self.getValueFields()))
            ShellAccess['valueFields'] = self.getValueFields()
        except:
            pass

    def camelCaseSplit(self, camelCaseStr, titleCase=False):
        matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', camelCaseStr)
        split = " ".join(m.group(0) for m in matches)
        if titleCase:
            return split.title()
        else:
            return split
