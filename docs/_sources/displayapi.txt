Display Data 
==============


Introduction
------------

PixieDust lets you visualize your data in just a few clicks. There's no need to write the complex code that you used to need to generate notebook graphs. Just call PixieDust's ``display()`` API, and any lay person can render and change complex table and chart displays. You can even choose from multiple rendering engines, without needing to know any of the code that makes them run. Watch this video demo:

.. raw:: html

    <div style="margin-top:10px; margin-bottom:25px;">
      <iframe width="560" height="315" src="http://www.youtube.com/embed/qetedQg8m3k" frameborder="0" allowfullscreen></iframe>
    </div><br>


.. sidebar:: Create your own

   PixieDust is extensible. If you don't see the display option you want, create it. You can write your own visualization plugin, using HTML, JavaScript, and CSS. `Read how <writeviz.html>`_.

The ``display()`` API  lets you visualize and chart your data in different ways. You can invoke the display API on any object, like a Spark DataFrame or Pandas DataFrame (support for additional formats is in development). PixieDust ``display()`` then introspects the object, determines what visualizations are capable of handling the data, and makes them available as menus within the output of the cell. If no visualization is found, then PixieDust ``display()`` shows an error message. Pixiedust display comes with a set of built-in visualizations like tables, bar charts, line charts, scatter plots, maps, and more. 


Get Started
-----------

Once you've imported the PixieDust module, start with the data. Here's some sample code that creates a data frame:

   ::

     #import pixiedust display module
     from pixiedust.display import *

     #Create a dataframe with Quarterly sales results
     sqlContext = SQLContext(sc)
     dd = sqlContext.createDataFrame(
          [(2010, 'Camping Equipment', 3),
          (2010, 'Golf Equipment', 1),
          (2010, 'Mountaineering Equipment', 1),
          (2010, 'Outdoor Protection', 2),
          (2010, 'Personal Accessories', 2),
          (2011, 'Camping Equipment', 4),
          (2011, 'Golf Equipment', 5),
          (2011, 'Mountaineering Equipment',2),
          (2011, 'Outdoor Protection', 4),
          (2011, 'Personal Accessories', 2),
          (2012, 'Camping Equipment', 5),
          (2012, 'Golf Equipment', 5),
          (2012, 'Mountaineering Equipment', 3),
          (2012, 'Outdoor Protection', 5),
          (2012, 'Personal Accessories', 3),
          (2013, 'Camping Equipment', 8),
          (2013, 'Golf Equipment', 5),
          (2013, 'Mountaineering Equipment', 3),
          (2013, 'Outdoor Protection', 8),
          (2013, 'Personal Accessories', 4)],
          ["year", "zone", "unique_customers"])

Then, in a single command, you  display that dataframe: ``dd``.
	
   ::

     #call a simple display api to visualize the data
     display(dd)


``display()`` looks up into its internal registry to build a list of visualizations that can handle a Spark DataFrame and generates the a menu toobar for each of them. The cell output looks like this:

.. container:: 

.. raw:: html

     <img src="https://github.com/DTAIEB/demos/raw/master/resources/PixieDust Sample Display.png" width="615" style="margin:30px 0px"><br>



.. sidebar:: Under the hood

   How does PixieDust generate this handy user interface? ``display()`` uses matplotlib to generate the charts and then mpld3 to transform the charts into D3 generated interactive charts that let users zoom, choose menus, see toolips, and more. 

PixieDust spins up a robust user interface that contains all the features you need to create sophisticated visualizations in just a few clicks. It contains  dropdown lists and dialogs you can use to change chart type, data content, grouping, and more. Without writing a line of code, you can:

- choose a display option: table, bar chart, pie chart, scatter plot, map, etc.
- set data content
- switch between rendering engines like matplotlib, seaborn, and bokeh
- zoom in for a more detailed view

``display()`` simplifies notebook charting in one important way: It takes only one cell to to generate hundreds of visualization options. Unlike traditional notebooks where you build a series of visualizations over several cells, PixieDust needs only one cell to generate an interactive widget which lets you turn knobs to explore the data in a myriad of ways.

DRAFT DRAFT DRAFT DRAFT  --docs in progress---

Work with Tables, Charts, and Maps
----------------------------------

Pixiedust ``display()`` provides an extensive set of graphs and visualizations. 

Tables
******

The resulting table shows extended information about the Spark DataFrame:  

 * **Schema** gives detailed information about the DataFrame schema
 * **Table** displays a sample of the data



Set Chart Content
*****************

You can configure the content of the chart by calling the options dialog available for each chart, using the Options button. The options dialog is composed of a set of commons options for every chart plus a set of additional options relevant to the currently selected chart.  

Here are the commons options for every charts:  

* Chart Title: display a title  
* Fields: available field name derived from the DataFrame schema  
* Keys: Name of the fields that will be used for the X-Axis  
* Values: Name of fields that will be user for the Y-Axis  
* Aggregation: Type of aggregation to be performed on the data  
	* SUM: sum of values for the key
	* AVG: average of values for the key
	* MIN: Min of values for the key
	* MAX: Max of values for the key
	* COUNT: number of times the key occurs  WHAT HAPPENS WHEN YOU LIMIT COUNT? HOW DOES PD CHOOSE RECORDS?

For example, Bar Chart shows the following options dialog:

.. container:: 

.. raw:: html

     <img src="https://github.com/DTAIEB/demos/raw/master/resources/PixieDust Options Dialog.png" width="615">


Bar Charts
**********

Bar charts are handy for comparing items side-by-side. When you select more than one key or value, you have the option to choose between 2 types of bar chart: 

* Stacked: items in a category are represented in a single column with different color for each segment  
* Grouped: items in a category are displayed side by side, making it easier to compare between each other.  

In our example, we use a Grouped bar chart showing the quarterly number of unique customers grouped by year:

.. container:: 

.. raw:: html

     <img src="https://github.com/DTAIEB/demos/raw/master/resources/PixieDust Bar Chart.png" width="615">


Line Chart
***********

.. container:: 

.. raw:: html

     <img src="https://github.com/DTAIEB/demos/raw/master/resources/PixieDust Line Chart.png" width="615">


Scatter Plot
*************

DRAFT

---docs in progress---

Pie Charts
**********

Map
***

Options: 
     Keys: Latitude, Longitude


Renderers: Mapbox, Google Maps.

USERS NEED MAPBOX KEY? - how handle?


Histogram
**********

Use a histogram if the values on your x-axis are numeric like age range, prices, etc... 

Conclusion
----------

Pixiedust display has a built-in set of chart visualizations that can render Spark and Pandas dataframe. The generated charts are easy to configure and also offer interactivity like Panning, zooming and tooltip. Pixiedust display() is also extensible and provide an API to let you write your own vizualizations.

