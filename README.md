# PixieDust

PixieDust is an open source Python helper library that works as an add-on to Jupyter notebooks to improve the user experience of working with data. It also provides extra capabilities that fill a gap when the notebook is hosted on the cloud and the user has no access to configuration files.

Its current capabilities include:

- **packageManager** lets you install spark packages inside a python notebook. This is something that you can't do today on hosted Jupyter notebooks, which prevents developers from using a large number of spark package add-ons.

- **visualizations.** One single API called `display()` lets you visualize your spark object in different ways: table, charts, maps, etc.... This module is designed to be extensible, providing an API that lets anyone easily contribute a new visualization plugin.
   
   This sample visualization plugin uses d3 to show the different flight routes for each airport:

   ![graph map](http://developer.ibm.com/clouddataservices/wp-content/uploads/sites/47/2016/07/pd_graphmap.png)

- **Export.** Download data to .csv, html, json, etc. locally on your laptop or into a variety of back-end data sources, like Cloudant, dashDB, GraphDB, etc...

   ![save as options](http://developer.ibm.com/clouddataservices/wp-content/uploads/sites/47/2016/07/pd_download.png)

- **Scala Bridge.** Use scala directly in your Python notebook. Variables are automatically transfered from Python to Scala and vice-versa

- **Extensibility.** Create your own visualizations using the pixiedust extensibility APIs. If you know html and css, you can write and deliver amazing graphics without forcing notebook users to type one line of code. Use the shape of the data to control when Pixiedust shows your visualization in a menu.

_**Note:** Pixiedust currently works with Spark 1.6 and Python 2.7._  
_**Note:** Pixiedust currently supports Spark DataFrames, Spark GraphFrames and Pandas DataFrames, with more to come. If you can't wait, write your own today and contribute it back._

Check out this detailed presentation of PixieDust:  
[![ScreenShot](https://i.ytimg.com/vi_webp/JcMefQ_o9oU/sddefault.webp)](https://www.youtube.com/embed/JcMefQ_o9oU?loop=1&amp;playlist=JcMefQ_o9oU)
