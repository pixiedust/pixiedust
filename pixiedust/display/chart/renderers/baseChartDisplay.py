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

from ..display import ChartDisplay
from abc import abstractmethod, ABCMeta
import traceback
import pixiedust
from six import PY2, with_metaclass
from pixiedust.display import addDisplayRunListener
from pixiedust.display.chart.renderers import PixiedustRenderer
from pixiedust.utils import cache,Logger
from pixiedust.utils.shellAccess import ShellAccess
import pandas as pd
import time

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
        if "cell_id" not in options:
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

@Logger()
class BaseChartDisplay(with_metaclass(ABCMeta, ChartDisplay)):

    def __init__(self, options, entity, dataHandler=None):
        super(BaseChartDisplay,self).__init__(options,entity,dataHandler)
        #note: since this class can be subclassed from other module, we need to mark the correct resource module with resModule so there is no mixup
        self.extraTemplateArgs["resModule"]=BaseChartDisplay.__module__

    """
        Subclass can override: return an array of option metadata
    """
    def getChartOptions(self):
        return []

    def getExtraFields(self):
        return []

    @cache(fieldName="workingPandasDataFrame")
    def getWorkingPandasDataFrame(self):
        xFields = self.getKeyFields()
        yFields = self.getValueFields()
        extraFields = self.getExtraFields()
        aggregation = self.getAggregation()
        maxRows = self.getMaxRows()
        #remember the constraints for this cache, they are the list of variables
        constraints = locals()

        workingDF = WorkingDataCache.getFromCache(self.options, constraints )
        if workingDF is None:
            workingDF = self.dataHandler.getWorkingPandasDataFrame(xFields, yFields, extraFields = extraFields, aggregation=aggregation, maxRows = maxRows )
            WorkingDataCache.putInCache(self.options, workingDF, constraints)
        
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

    def getPandasDataFrame(self):
        valueFieldValues = self.getValueFieldValueLists()
        valueFields = self.getValueFields()
        return pd.DataFrame([list(a) for a in zip( valueFieldValues[0], valueFieldValues[1]) ], columns=[valueFields[0], valueFields[1]])

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

    @cache(fieldName="keyFieldValues")
    def getKeyFieldValues(self):
        """ Get the DATA for the dataframe key fields

        Args: 
            self (class): class that extends BaseChartDisplay

        Returns: 
            List of lists: data for the key fields
        """
        keyFields = self.getKeyFields()
        if (len(keyFields) == 0):
            return []
        numericKeyField = False
        if len(keyFields) == 1 and self.dataHandler.isNumericField(keyFields[0]):
            numericKeyField = True
        df = self.dataHandler.groupBy(keyFields).count().dropna()
        if self.isMap(self.handlerId) is False: 
            for keyField in keyFields:
                df = df.sort(keyField)
        maxRows = int(self.options.get("rowCount","100"))
        numRows = min(maxRows,df.count())
        rows = df.take(numRows)
        values = []
        for i, row in enumerate(rows):
            if numericKeyField:
                values.append(row[keyFields[0]])
            else:
                values.append(i)
        return values

    @cache(fieldName="keyFieldLabels")
    def getKeyFieldLabels(self):
        keyFields = self.getKeyFields()
        if (len(keyFields) == 0):
            return []
        return self.getWorkingPandasDataFrame().groupby(keyFields).groups.keys()
        """df = self.dataHandler.groupBy(keyFields).count().dropna()
        for keyField in keyFields:
            df = df.sort(keyField)
        maxRows = int(self.options.get("rowCount","100"))
        numRows = min(maxRows,df.count())
        rows = df.take(numRows)
        labels = []
        for i, row in enumerate(rows):
            label = ""
            for keyField in keyFields:
                if len(label) > 0:
                    label += ", "
                label += str(row[keyField])
            labels.append(label)
        return labels"""

    def getPreferredDefaultValueFieldCount(self, handlerId):
        return 2

    @cache(fieldName="valueFields")   
    def getValueFields(self):
        fieldNames = self.getFieldNames()
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
        return numericValueFields

    def getPandasValueFieldValueLists(self):
        keyFields = self.getKeyFields()
        valueFields = self.getValueFields()
        aggregation = self.getAggregation()
        pandasValueLists = []
        maxRows = int(self.options.get("rowCount","100"))
        if len(keyFields) == 0:
            for valueField in valueFields:
                pandasValueLists.append(
                    self.dataHandler.select(valueField).toPandas()[valueField].dropna().head(maxRows)
                )
        else:
            df = self.dataHandler.groupBy(keyFields)
            maxRows = int(self.options.get("rowCount","100"))
            for valueField in valueFields:
                valueDf = None
                if aggregation == "SUM":
                    valueDf = df.agg({valueField:"sum"}).withColumnRenamed("sum("+valueField+")", "agg")
                elif aggregation == "AVG":
                    valueDf = df.agg({valueField:"avg"}).withColumnRenamed("avg("+valueField+")", "agg")
                elif aggregation == "MIN":
                    valueDf = df.agg({valueField:"min"}).withColumnRenamed("min("+valueField+")", "agg")
                elif aggregation == "MAX":
                    valueDf = df.agg({valueField:"max"}).withColumnRenamed("max("+valueField+")", "agg")
                else:
                    valueDf = df.agg({valueField:"count"}).withColumnRenamed("count("+valueField+")", "agg")
                #for keyField in keyFields:
                #    valueDf = valueDf.sort(keyField)
                valueDf = valueDf.dropna()
                numRows = min(maxRows,valueDf.count())
                pandasValueLists.append( valueDf.toPandas().head(numRows) )
        return pandasValueLists

    @cache(fieldName="valueFieldValueLists")
    def getValueFieldValueLists(self):
        keyFields = self.getKeyFields()
        valueFields = self.getValueFields()
        aggregation = self.getAggregation()
        valueLists = []
        maxRows = int(self.options.get("rowCount","100"))
        if len(keyFields) == 0:
            valueLists = []
            for valueField in valueFields:
                valueLists.append(
                    self.dataHandler.select(valueField).toPandas()[valueField].dropna().tolist()[:maxRows]
                )
        #elif self.supportsAggregation(handlerId) == False:
        #    for valueField in valueFields:
                # TODO: Need to get the list of values per unique key (not count, avg, etc)
                # For example, SELECT distinct key1, key2 FROM table
                # for each key1/key2 SELECT value1 FROM table WHERE key1=key1 AND key2=key2
                # for each key1/key2 SELECT value2 FROM table WHERE key1=key1 AND key2=key2
                # repeat for each value
        else:
            df = self.dataHandler.groupBy(keyFields)
            maxRows = int(self.options.get("rowCount","100"))
            for valueField in valueFields:
                valueDf = None
                if aggregation == "SUM":
                    valueDf = df.agg({valueField:"sum"}).withColumnRenamed("sum("+valueField+")", "agg")
                elif aggregation == "AVG":
                    valueDf = df.agg({valueField:"avg"}).withColumnRenamed("avg("+valueField+")", "agg")
                elif aggregation == "MIN":
                    valueDf = df.agg({valueField:"min"}).withColumnRenamed("min("+valueField+")", "agg")
                elif aggregation == "MAX":
                    valueDf = df.agg({valueField:"max"}).withColumnRenamed("max("+valueField+")", "agg")
                else:
                    valueDf = df.agg({valueField:"count"}).withColumnRenamed("count("+valueField+")", "agg")
                if self.isMap(self.handlerId) is False: 
                    for keyField in keyFields:
                        valueDf = valueDf.sort(keyField)
                valueDf = valueDf.dropna()
                numRows = min(maxRows,valueDf.count())
                valueLists.append(valueDf.rdd.map(lambda r:r["agg"]).take(numRows))
        return valueLists
    
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
        return PixiedustRenderer.getRendererList(self.options, self.entity)

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

    def doRender(self, handlerId):
        self.handlerId = handlerId

        if self.options.get("debug", None):
            self.logStuff()

        # field names
        fieldNames = self.getFieldNames(True)
        (dialogTemplate, dialogOptions) = self.getDialogInfo(handlerId)

        # go
        try:
            keyFields = self.getKeyFields()
            valueFields = self.getValueFields()
        except ShowChartOptionDialog:
            self.dialogBody = self.renderTemplate(dialogTemplate, **dialogOptions)
            self._addJavascriptTemplate("chartOptions.dialog", optionsDialogBody=self.dialogBody)
            return
        
        # validate if we can render
        canRender, errorMessage = self.canRenderChart()
        if canRender == False:
            self.dialogBody = self.getChartErrorDialogBody(handlerId, dialogTemplate, dialogOptions)
            if (self.dialogBody is None):
                self.dialogBody = ""
            self._addHTMLTemplate("chartError.html", errorMessage=errorMessage, optionsDialogBody=self.dialogBody)
            return

        # set the keyFields and valueFields options if this is the first time
        # do this after call to canRenderChart as some charts may need to know that they have not been set
        setKeyFields = self.options.get("keyFields") is None
        setValueFields = self.options.get("valueFields") is None
        if setKeyFields and len(keyFields) > 0:
            self.options["keyFields"] = ",".join(keyFields)
        if setValueFields and len(valueFields) > 0:
            self.options["valueFields"] = ",".join(valueFields)
        
        # render
        try:
            self.dialogBody = self.renderTemplate(dialogTemplate, **dialogOptions)
            chartFigure = self.doRenderChart()
            if self.options.get("debugFigure", None):
                self.debug(chartFigure)
            if self.options.get("nostore_figureOnly", None):
                self._addHTML(chartFigure)
            else:
                self._addHTMLTemplate("renderer.html", chartFigure=chartFigure, optionsDialogBody=self.dialogBody)
        except Exception as e:
            self.exception("Unexpected error while trying to render BaseChartDisplay")
            self.dialogBody = self.getChartErrorDialogBody(handlerId, dialogTemplate, dialogOptions)
            if (self.dialogBody is None):
                self.dialogBody = ""
            self._addHTMLTemplate("chartError.html", errorMessage="Unexpected Error:<br>"+str(e), optionsDialogBody=self.dialogBody)
            self.info("Unexpected Error:\n"+str(e)+"\n\n"+traceback.format_exc())

    def logStuff(self):
        try:
            self.debug("Key Fields: {0}".format(self.getKeyFields()) )
            #self.debug("Key Fields Values: {0}".format(self.getKeyFieldValues()))
            self.debug("Key Fields Labels: {0}".format(self.getKeyFieldLabels()))
        except:
            pass
        try:
            self.debug("Value Fields: {0}".format(self.getValueFields()))
            #self.debug("Value Field Values List: {0}".format(self.getValueFieldValueLists()))
        except:
            pass