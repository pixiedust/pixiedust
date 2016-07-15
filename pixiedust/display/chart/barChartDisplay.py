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
import matplotlib.pyplot as plt
import numpy as np
from mpld3 import plugins
from mpld3 import utils
from pyspark.sql import functions as F
import mpld3


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



class BarChartDisplay(ChartDisplay):
    def doRender(self, handlerId):
        
        
        displayColName = self.getFirstNumericalColInfo()
        if not displayColName:
            return self._addHTML("Unable to find a numerical column in the dataframe")
            
        
        import mpld3
        mpld3.enable_notebook()     
        fig = plt.figure()
        params = plt.gcf()
        plSize = params.get_size_inches()
        params.set_size_inches( (plSize[0]*2, plSize[1]*2) )
        

        if ( (self.options.get("agg",False))==True):
            aggType=self.options.get("aggType")
            if(aggType=='average'):
                colLabel = self.options.get("groupBy")
                # group by 'displayColName' -> aggregate 'displayColName' by avg -> set column alias as 'avg'  
                y1 = self.entity.groupBy(colLabel).agg(F.avg(displayColName).alias("avg")).toPandas()
                # take column 'avg' remove NAs and convert to a list
                y = y1["avg"].dropna().tolist()
                #arrange() creates intervals for the axis eg: np.arange(3) -> array([0, 1, 2])
                x_intv = np.arange(len(y))
                labels =  self.entity.select(colLabel).toPandas()[colLabel].dropna().tolist()
                # plot the x-axis with intervals and their respective labels 
                plt.xticks(x_intv,labels)
                # Label the x and y axis
                plt.xlabel(colLabel, fontsize=18)
                plt.ylabel("Average "+displayColName, fontsize=18)
            elif(aggType=='sum'):
                colLabel = self.options.get("groupBy")
                # group by 'displayColName' -> aggregate 'displayColName' by sum -> set column alias as 'sum'  
                y1 = self.entity.groupBy(colLabel).agg(F.sum(displayColName).alias("sum")).toPandas()
                # take column 'avg' remove NAs and convert to a list
                y = y1["sum"].dropna().tolist()
                #arrange() creates intervals for the axis eg: np.arange(3) -> array([0, 1, 2])
                x_intv = np.arange(len(y))
                labels =  self.entity.select(colLabel).toPandas()[colLabel].dropna().tolist()
                # plot the x-axis with intervals and their respective labels 
                plt.xticks(x_intv,labels)
                # Label the x and y axis
                plt.xlabel(colLabel, fontsize=18)
                plt.ylabel("Sum of "+displayColName, fontsize=18)
            elif(aggType=='count'):
                colLabel = self.options.get("groupBy")
                # group by 'displayColName' -> aggregate 'displayColName' by count -> set column alias as 'count'  
                y1 = self.entity.groupBy(colLabel).agg(F.count(displayColName).alias("count")).toPandas()
                # take column 'avg' remove NAs and convert to a list
                y = y1["count"].dropna().tolist()
                #arrange() creates intervals for the axis eg: np.arange(3) -> array([0, 1, 2])
                x_intv = np.arange(len(y))
                labels =  self.entity.select(colLabel).toPandas()[colLabel].dropna().tolist()
                # plot the x-axis with intervals and their respective labels 
                plt.xticks(x_intv,labels)
                # Label the x and y axis
                plt.xlabel(colLabel, fontsize=18)
                plt.ylabel("(Count) "+displayColName, fontsize=18)    
            else:
                return self._addHTML("aggType argument not mentioned.")
        else:
            colLabel = self.getFirstStringColInfo()
            # Taking data as it is for plotting Bar Chart i.e. without aggregating 
            y = self.entity.select(displayColName).toPandas()[displayColName].dropna().tolist()
            #arrange() creates intervals for the axis eg: np.arange(3) -> array([0, 1, 2])
            x_intv = np.arange(len(y))
            labels =  self.entity.select(colLabel).toPandas()[colLabel].dropna().tolist()
            # plot the x-axis with intervals and their respective labels 
            plt.xticks(x_intv,labels)
            # Label the x and y axis
            plt.xlabel(colLabel, fontsize=18)
            plt.ylabel(displayColName, fontsize=18)
       
        
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