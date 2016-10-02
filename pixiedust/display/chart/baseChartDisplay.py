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

from .display import ChartDisplay
from .plugins.chart import ChartPlugin
from .plugins.dialog import DialogPlugin
from abc import abstractmethod
from pyspark.sql import functions as F
from pyspark.sql.types import StructType
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import mpld3
import mpld3.plugins as plugins
import traceback
import pixiedust.utils.dataFrameMisc as dataFrameMisc
import pixiedust

myLogger = pixiedust.getLogger(__name__)

class BaseChartDisplay(ChartDisplay):

    def getChartContext(self, handlerId):
        return None

    def getChartErrorDialogBody(self, handlerId, dialogTemplate, dialogOptions):
        return self.renderTemplate(dialogTemplate, **dialogOptions)

    @abstractmethod
    def doRenderChart(self, handlerId, dialogTemplate, dialogOptions, aggregation, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues):
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

    def getDefaultKeyFields(self, handlerId, aggregation):
        if self.supportsKeyFields(handlerId) == False:
            return []
        defaultFields = []
        for field in self.entity.schema.fields:
            if (dataFrameMisc.isNumericType(field.dataType) == False and field.name.lower() != "id"):
                defaultFields.append(field.name)
                if len(defaultFields) == self.getPreferredDefaultKeyFieldCount(handlerId):
                    break
        if len(defaultFields) == 0:
            defaultFields.append(self.entity.schema.fields[0].name)
        return defaultFields

    def getKeyFields(self, handlerId, aggregation, fieldNames):
        if self.supportsKeyFields(handlerId) == False:
            return []
        keyFields = []
        keyFieldStr = self.options.get("keyFields")
        if keyFieldStr is not None:
            keyFields = keyFieldStr.split(",")
            keyFields = [val for val in keyFields if val in fieldNames]
        if len(keyFields) == 0:
            return self.getDefaultKeyFields(handlerId, aggregation)
        else:
            return keyFields

    def getKeyFieldValues(self, handlerId, aggregtaion, keyFields):
        if (len(keyFields) == 0):
            return []
        numericKeyField = False
        if (len(keyFields) == 1 and self.isNumericField(keyFields[0])):
            numericKeyField = True
        df = self.entity.groupBy(keyFields).count().dropna()
        for keyField in keyFields:
            df = df.sort(F.col(keyField).asc())
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

    def getKeyFieldLabels(self, handlerId, aggregtaion, keyFields):
        if (len(keyFields) == 0):
            return []
        df = self.entity.groupBy(keyFields).count().dropna()
        for keyField in keyFields:
            df = df.sort(F.col(keyField).asc())
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

    def getDefaultValueFields(self, handlerId, aggregation):
        fieldNames = []
        for field in self.entity.schema.fields:
            if dataFrameMisc.isNumericType(field.dataType):
                fieldNames.append(field.name)
                if len(fieldNames) == self.getPreferredDefaultValueFieldCount(handlerId):
                    break
        return fieldNames
        
    def getValueFields(self, handlerId, aggregation, fieldNames):
        valueFields = []
        valueFieldStr = self.options.get("valueFields")
        if valueFieldStr is not None:
            valueFields = valueFieldStr.split(",")
            valueFields = [val for val in valueFields if val in fieldNames]
        if len(valueFields) == 0:
            valueFields = self.getDefaultValueFields(handlerId, aggregation)
        numericValueFields = []
        for valueField in valueFields:
            if self.isNumericField(valueField) or aggregation == "COUNT":
                numericValueFields.append(valueField)
        return numericValueFields

    def getValueFieldValueLists(self, handlerId, aggregation, keyFields, valueFields):
        valueLists = []
        maxRows = int(self.options.get("rowCount","100"))
        if len(keyFields) == 0:
            valueLists = []
            for valueField in valueFields:
                valueLists.append(self.entity.select(F.col(valueField).alias(valueField)).toPandas()[valueField].dropna().tolist()[:maxRows])
        #elif self.supportsAggregation(handlerId) == False:
        #    for valueField in valueFields:
                # TODO: Need to get the list of values per unique key (not count, avg, etc)
                # For example, SELECT distinct key1, key2 FROM table
                # for each key1/key2 SELECT value1 FROM table WHERE key1=key1 AND key2=key2
                # for each key1/key2 SELECT value2 FROM table WHERE key1=key1 AND key2=key2
                # repeat for each value
        else:
            df = self.entity.groupBy(keyFields)
            maxRows = int(self.options.get("rowCount","100"))
            numRows = min(maxRows,df.count())
            for valueField in valueFields:
                valueDf = None
                if aggregation == "SUM":
                    valueDf = df.agg(F.sum(valueField).alias("agg"))
                elif aggregation == "AVG":
                    valueDf = df.agg(F.avg(valueField).alias("agg"))
                elif aggregation == "MIN":
                    valueDf = df.agg(F.min(valueField).alias("agg"))
                elif aggregation == "MAX":
                    valueDf = df.agg(F.max(valueField).alias("agg"))
                else:
                    valueDf = df.agg(F.count(valueField).alias("agg"))
                for keyField in keyFields:
                    valueDf = valueDf.sort(F.col(keyField).asc())
                valueDf = valueDf.dropna()
                rows = valueDf.select("agg").take(numRows)
                valueList = []
                for row in rows:
                    valueList.append(row["agg"])
                valueLists.append(valueList)
        return valueLists   

    def setChartSize(self, handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues):
        params = plt.gcf()
        plSize = params.get_size_inches()
        params.set_size_inches((plSize[0]*1.5, plSize[1]*1.5))
        
    def setChartGrid(self, handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues):
        ax.grid(color='lightgray', alpha=0.7)

    def setChartTitle(self, handlerId):
        title = self.options.get("title")
        if title is not None:
            plt.title(title, fontsize=30)

    def setChartLegend(self, handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues):
        if self.supportsLegend(handlerId):
            showLegend = self.options.get("showLegend", "true")
            if showLegend == "true":
                l = ax.legend(title=self.titleLegend if hasattr(self, 'titleLegend') else '')
                if l is not None:
                    l.get_frame().set_alpha(0)
                    numColumns = len(keyFieldValues)
                    for i, text in enumerate(l.get_texts()):
                        text.set_color(colormap(1.*i/numColumns))
                    for i, line in enumerate(l.get_lines()):
                        line.set_color(colormap(1.*i/numColumns))
                        line.set_linewidth(10)
    
    def canRenderChart(self, handlerId, aggregation, fieldNames):
        if (aggregation == "COUNT"):
            return (True, None)
        else:
            for field in self.entity.schema.fields:
                if dataFrameMisc.isNumericType(field.dataType):
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

    def doRender(self, handlerId):
        # field names
        fieldNames = self.getFieldNames(True)
        
        # get aggregation value (set to default if it doesn't exist)
        aggregation = self.options.get("aggregation")
        if (aggregation is None and self.supportsAggregation(handlerId)):
            aggregation = self.getDefaultAggregation(handlerId)
            self.options["aggregation"] = aggregation

        # go
        keyFields = self.getKeyFields(handlerId, aggregation, fieldNames)
        keyFieldValues = self.getKeyFieldValues(handlerId, aggregation, keyFields)
        keyFieldLabels = self.getKeyFieldLabels(handlerId, aggregation, keyFields)
        valueFields = self.getValueFields(handlerId, aggregation, fieldNames)
        valueFieldValues = self.getValueFieldValueLists(handlerId, aggregation, keyFields, valueFields)

        (dialogTemplate, dialogOptions) = self.getDialogInfo(handlerId)
        
        # validate if we can render
        canRender, errorMessage = self.canRenderChart(handlerId, aggregation, fieldNames)
        if canRender == False:
            dialogBody = self.getChartErrorDialogBody(handlerId, dialogTemplate, dialogOptions)
            if (dialogBody is None):
                dialogBody = ""
            self._addHTMLTemplate("chartError.html", errorMessage=errorMessage, optionsDialogBody=dialogBody)
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
            self.doRenderChart(handlerId, dialogTemplate, dialogOptions, aggregation, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues)
        except Exception, e:
            myLogger.exception("Unexpected error while trying to render BaseChartDisplay")
            dialogBody = self.getChartErrorDialogBody(handlerId, dialogTemplate, dialogOptions)
            if (dialogBody is None):
                dialogBody = ""
            self._addHTMLTemplate("chartError.html", errorMessage="Unexpected Error:<br>"+str(e), optionsDialogBody=dialogBody)
            #self._addHTMLTemplate("chartError.html", errorMessage="Unexpected Error:<br>"+str(e)+"<br><br><pre>"+traceback.format_exc()+"</pre>", optionsDialogBody=dialogBody)

    def getFieldNames(self, expandNested=False):
        return dataFrameMisc.getFieldNames(self.entity, expandNested)

    def isNumericField(self, fieldName):
        return dataFrameMisc.isNumericField(self.entity, fieldName)