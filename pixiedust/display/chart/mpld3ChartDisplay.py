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
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import mpld3
import mpld3.plugins as plugins

class Mpld3ChartDisplay(ChartDisplay):

    def getMpld3Context(self, handlerId):
        return None

    @abstractmethod
    def doRenderMpld3(self, handlerId, fig, ax, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues):
        pass

    def supportsLegend(self, handlerId):
        return True

    def supportsAggregation(self, handlerId):
        return True

    def getDefaultAggregation(self, handlerId):
        return "SUM"

    def getDefaultKeyFields(self, handlerId, aggregation):
        defaultFields = []
        for field in self.entity.schema.fields:
            type = field.dataType.__class__.__name__
            if (type != "LongType" and type != "IntegerType" and field.name.lower() !="id"):
                defaultFields.append(field.name)
                break
        if len(defaultFields) == 0:
            defaultFields.append(self.entity.schema.fields[0].name)
        return defaultFields

    def getKeyFields(self, handlerId, aggregation):
        keyFields = self.options.get("keyFields")
        if keyFields is not None:
            return keyFields.split(",")
        else:
            return self.getDefaultKeyFields(handlerId, aggregation)

    def getKeyFieldValues(self, handlerId, aggregtaion, keyFields):
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

    def defaultToSingleValueField(self, handlerId):
		return False

    def getDefaultValueFields(self, handlerId, aggregation):
        fieldNames = []
        for field in self.entity.schema.fields:
            type = field.dataType.__class__.__name__
            if ( type =="LongType" or type == "IntegerType" ):
                fieldNames.append(field.name)
                if self.defaultToSingleValueField(handlerId):
                    break
        return fieldNames
        
    def getValueFields(self, handlerId, aggregation):
        if self.options.get("valueFields") is not None:
            valueFields = self.options.get("valueFields").split(",")
        else:
            valueFields = self.getDefaultValueFields(handlerId, aggregation)
        numericValueFields = []
        for valueField in valueFields:
            if self.isNumericField(valueField) or aggregation == "COUNT":
                numericValueFields.append(valueField)
        return numericValueFields

    def getValueFieldValueLists(self, handlerId, aggregation, keyFields, valueFields):
        df = self.entity.groupBy(keyFields)
        maxRows = int(self.options.get("rowCount","100"))
        numRows = min(maxRows,df.count())
        valueLists = []
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

    def setChartLegend(self, handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues):
        if self.supportsLegend(handlerId):
            showLegend = self.options.get("showLegend", "true")
            if showLegend == "true":
                l = ax.legend(title='')
                numColumns = len(keyFieldValues)
                for i, text in enumerate(l.get_texts()):
                    text.set_color(colormap(1.*i/numColumns))
                for i, line in enumerate(l.get_lines()):
                    line.set_color(colormap(1.*i/numColumns))
                    line.set_linewidth(10)
    
    def canRenderChart(self, handlerId):
        for field in self.entity.schema.fields:
            type = field.dataType.__class__.__name__
            if ( type =="LongType" or type == "IntegerType" ):
                return True
        return False

    def doRender(self, handlerId):
        if self.canRenderChart(handlerId) == False:
            self._addHTML("Unable to find a numerical column in the dataframe")
            return

        mpld3.enable_notebook()
        fig, ax = plt.subplots()
        aggregation = self.options.get("aggregation")
        if (aggregation is None):
            aggregation = self.getDefaultAggregation(handlerId)
            self.options["aggregation"] = aggregation
        keyFields = self.getKeyFields(handlerId, aggregation)
        keyFieldValues = self.getKeyFieldValues(handlerId, aggregation, keyFields)
        keyFieldLabels = self.getKeyFieldLabels(handlerId, aggregation, keyFields)
        valueFields = self.getValueFields(handlerId, aggregation)
        valueFieldValues = self.getValueFieldValueLists(handlerId, aggregation, keyFields, valueFields)
        context = self.getMpld3Context(handlerId)
        options = {"fieldNames":self.getFieldNames(),"legendSupported":self.supportsLegend(handlerId),"aggregationSupported":self.supportsAggregation(handlerId),"aggregationOptions":["SUM","AVG","MIN","MAX","COUNT"]}
        if (context is not None):
            options.update(context[1])
            dialogBody = self.renderTemplate(context[0], **options)
        else:
            dialogBody = self.renderTemplate("baseChartOptionsDialogBody.html", **options)
        plugins.connect(fig, ChartPlugin(self, keyFieldLabels))
        plugins.connect(fig, DialogPlugin(self, handlerId, dialogBody))
        colormap = cm.jet
        self.doRenderMpld3(handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues)
        self.setChartSize(handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues)
        self.setChartGrid(handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues)
        self.setChartLegend(handlerId, fig, ax, colormap, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues)

    def getFieldNames(self):
        fieldNames = []
        for field in self.entity.schema.fields:
            fieldNames.append(field.name)
        return fieldNames

    def isNumericField(self, fieldName):
        for field in self.entity.schema.fields:
            if (field.name == fieldName):
                type = field.dataType.__class__.__name__
                if ( type =="LongType" or type == "IntegerType" ):
                    return True
        return False
	