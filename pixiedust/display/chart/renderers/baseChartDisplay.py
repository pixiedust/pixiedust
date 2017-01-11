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
from pixiedust.display.chart.renderers import PixiedustRenderer
from pixiedust.utils import cache

myLogger = pixiedust.getLogger(__name__)

class ShowChartOptionDialog(Exception):
    pass

class BaseChartDisplay(with_metaclass(ABCMeta, ChartDisplay)):

    def __init__(self, options, entity, dataHandler=None):
        super(BaseChartDisplay,self).__init__(options,entity,dataHandler)
        #note: since this class can be subclassed from other module, we need to mark the correct resource module with resModule so there is no mixup
        self.extraTemplateArgs["resModule"]=BaseChartDisplay.__module__

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
        fieldNames = self.getFieldNames()
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
        keyFields = self.getKeyFields()
        if (len(keyFields) == 0):
            return []
        numericKeyField = False
        if len(keyFields) == 1 and self.dataHandler.isNumericField(keyFields[0]):
            numericKeyField = True
        df = self.dataHandler.groupBy(keyFields).count().dropna()
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
        df = self.dataHandler.groupBy(keyFields).count().dropna()
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
        return labels

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
                for keyField in keyFields:
                    valueDf = valueDf.sort(keyField)
                valueDf = valueDf.dropna()
                numRows = min(maxRows,valueDf.count())
                rows = valueDf.select("agg").take(numRows)
                valueList = []
                for row in rows:
                    valueList.append(row["agg"])
                valueLists.append(valueList)
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
        # get aggregation value (set to default if it doesn't exist)
        aggregation = self.options.get("aggregation")
        if (aggregation is None and self.supportsAggregation(self.handlerId)):
            aggregation = self.getDefaultAggregation(handlerId)
            self.options["aggregation"] = aggregation
        return aggregation

    @cache(fieldName="fieldNames")
    def getFieldNames(self, expandNested=True):
        return self.dataHandler.getFieldNames(expandNested)

    def doRender(self, handlerId):
        self.handlerId = handlerId

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
            self._addHTMLTemplate("renderer.html", chartFigure=chartFigure, optionsDialogBody=self.dialogBody)
        except Exception as e:
            myLogger.exception("Unexpected error while trying to render BaseChartDisplay")
            self.dialogBody = self.getChartErrorDialogBody(handlerId, dialogTemplate, dialogOptions)
            if (self.dialogBody is None):
                self.dialogBody = ""
            self._addHTMLTemplate("chartError.html", errorMessage="Unexpected Error:<br>"+str(e), optionsDialogBody=self.dialogBody)
            myLogger.info("Unexpected Error:\n"+str(e)+"\n\n"+traceback.format_exc())