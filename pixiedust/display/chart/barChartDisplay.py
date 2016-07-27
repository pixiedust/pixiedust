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
from .mpld3ChartDisplay import Mpld3ChartDisplay
import matplotlib.pyplot as plt
import numpy as np
import mpld3.plugins as plugins
from mpld3 import utils
from pyspark.sql import functions as F
import mpld3
from .plugins.dialog import DialogPlugin
from random import randint

class BarChart(mpld3.plugins.PluginBase):  # inherit from PluginBase
    """Bar chart plugin to fix xticks that are overriden by mpld3 while converting from matplotlib """
    
    JAVASCRIPT = """
    mpld3.register_plugin("barchart", BarChart);
    BarChart.prototype = Object.create(mpld3.Plugin.prototype);
    BarChart.prototype.constructor = BarChart;
    BarChart.prototype.requiredProps = ["labels"];
    function BarChart(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };
    
    BarChart.prototype.draw = function(){
        // FIXME: this is a very brittle way to select the x-axis element
        var ax = this.fig.axes[0].elements[0];

        // getting the labels for xticks
        var labels =  this.props.labels;
        console.info("labels: "+labels);
        
        // see https://github.com/mbostock/d3/wiki/Formatting#d3_format
        // for d3js formating documentation
        ax.axis.tickFormat(function(d){return labels[d]});
        ax.axis.ticks(labels.length);

        // HACK: use reset to redraw figure
        this.fig.reset(); 
    }
    """
    def __init__(self,labels):
        self.dict_ = {"type": "barchart","labels": labels }



class BarChartDisplay(Mpld3ChartDisplay):
    # override if you need to add custom form fields
    def getMpld3Context(self, handlerId):
        return ("barChartOptionsDialogBody.html",{"colNames":self.getFieldNames()})
    def doRenderMpld3(self, handlerId, figure, axes, keyFields, keyFieldValues, keyFieldLabels, valueFields, valueFieldValues):
        allNumericCols = self.getNumericalFieldNames()
        if len(allNumericCols) == 0:
            self._addHTML("Unable to find a numerical column in the dataframe")
            return
        
                 
        keyFields = self.options.get("keyFields")
        valueField = self.options.get("valueFields")

        if(keyFields==None and valueField==None):
            keyFields=self.getFirstStringColInfo()
            valueField=self.getFirstNumericalColInfo() 
        else:
            keyFields = keyFields.split(',') 
            valueField = valueField.split(',') 
            if(len(valueField) > 1):
                self._addHTML("You can enter only have one value field for Bar Charts (2-D)"+str(len(valueField)))
                return
            keyFields = keyFields[0]
            valueField=valueField[0]
        
                
        #if(len(valueFields>)):


    
        #init
        fig=figure
        ax=axes
        
        #fig, ax = plt.subplots()   
        #fig = plt.figure()
        

        params = plt.gcf()
        plSize = params.get_size_inches()
        params.set_size_inches( (plSize[0]*2, plSize[1]*2) )


        agg=self.options.get("aggregation")
        groupByCol=self.options.get("groupByCol")
        
        if (agg=="None" or agg==None):
            colLabel = keyFields
            y = self.entity.select(valueField).toPandas()[valueField].dropna().tolist()
            x_intv = np.arange(len(y))
            labels =  self.entity.select(keyFields).toPandas()[keyFields].dropna().tolist()
            plt.xticks(x_intv,labels)
            plt.xlabel(keyFields, fontsize=18)
            plt.ylabel(valueField, fontsize=18)
        elif(agg=='AVG'):
            y1=self.entity.groupBy(keyFields).agg(F.avg(valueField).alias("avg")).toPandas().sort_values(by=keyFields)
            y=y1["avg"].dropna().tolist()
            x_intv = np.arange(len(y))
            labels=y1[keyFields].dropna().tolist()
            plt.xticks(x_intv,labels)
            plt.xlabel(keyFields, fontsize=18)
            plt.ylabel("Average "+valueField, fontsize=18)
        elif(agg=='SUM'):
            y1=self.entity.groupBy(keyFields).agg(F.sum(valueField).alias("sum")).toPandas().sort_values(by=keyFields)
            y=y1["sum"].dropna().tolist()
            x_intv = np.arange(len(y))
            labels=y1[keyFields].dropna().tolist()
            plt.xticks(x_intv,labels)
            plt.xlabel(keyFields, fontsize=18)
            plt.ylabel("sum "+valueField, fontsize=18)
        elif(agg=='MAX'):
            y1=self.entity.groupBy(keyFields).agg(F.max(valueField).alias("max")).toPandas().sort_values(by=keyFields)
            y=y1["max"].dropna().tolist()
            x_intv = np.arange(len(y))
            labels=y1[keyFields].dropna().tolist()
            plt.xticks(x_intv,labels)
            plt.xlabel(keyFields, fontsize=18)
            plt.ylabel("max "+valueField, fontsize=18)
        elif(agg=='MIN'):
            y1=self.entity.groupBy(keyFields).agg(F.min(valueField).alias("min")).toPandas().sort_values(by=keyFields)
            y=y1["min"].dropna().tolist()
            x_intv = np.arange(len(y))
            labels=y1[keyFields].dropna().tolist()
            plt.xticks(x_intv,labels)
            plt.xlabel(keyFields, fontsize=18)
            plt.ylabel("min "+valueField, fontsize=18)
        elif(agg=='COUNT'):
            y1=self.entity.groupBy(keyFields).agg(F.count(valueField).alias("count")).toPandas().sort_values(by=keyFields)
            y=y1["count"].dropna().tolist()
            x_intv = np.arange(len(y))
            labels=y1[keyFields].dropna().tolist()
            plt.xticks(x_intv,labels)
            plt.xlabel(keyFields, fontsize=18)
            plt.ylabel("count "+valueField, fontsize=18)

        mpld3.enable_notebook()      
        plt.bar(x_intv,y,color="blue",alpha=0.5)
        ax_fmt = BarChart(labels)
        mpld3.plugins.connect(fig, ax_fmt)
        
    def getFirstNumericalColInfo(self):
        # Gets the first numerical column in the dataframe that is of either Long or IntegerType
        schema = self.entity.schema
        for field in schema.fields:
            type = field.dataType.__class__.__name__
            if ( type =="LongType" or type == "IntegerType" ):
                return field.name
   
    def getFirstStringColInfo(self):
        # Gets the first non numerical column in the dataframe 
        schema = self.entity.schema
        for field in schema.fields:
            type = field.dataType.__class__.__name__
            if (type != "LongType" and type != "IntegerType" and field.name.lower() !="id"):
                return field.name
    
    def getNumericalFieldNames(self):
        schema = self.entity.schema
        fieldNames = []
        for field in schema.fields:
            type = field.dataType.__class__.__name__
            if ( type =="LongType" or type == "IntegerType" ):
                fieldNames.append(field.name)
        return fieldNames