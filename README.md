# pixiedust

Pixiedust is an open source Python helper library that works as an add-on to Jupyter notebooks to improve the user experience of working with data. It also provides extra capabilities that fill a gap when the notebook is hosted on the cloud and the user has no access to configuration files.

Its current capabilities include:

- **packageManager** lets you install spark packages inside a python notebook. This is something that you can't do today on hosted Jupyter notebooks, which prevents developers from using a large number of spark package add-ons.
The following code installs the GraphFrames spark package into your IPython notebook
   ```
from pixiedust.packageManager import PackageManager
pkg=PackageManager()
pkg.installPackage("graphframes:graphframes:0")
   ```

- **visualizations.** One single API called `display` lets you visualize your spark object in different ways: table, charts, maps, etc.... This module is designed to be extensible, providing an API that lets anyone easily contribute a new visualization plugin.
   
   This sample visualization plugin uses d3 to show the different flight routes for each airport:

   ![graph map](http://developer.ibm.com/clouddataservices/wp-content/uploads/sites/47/2016/07/pd_graphmap.png)

- **service integration.** Stash data into a variety of back-end data sources, like Cloudant, dashDB, GraphDB, etc...

   ![save as options](http://developer.ibm.com/clouddataservices/wp-content/uploads/sites/47/2016/07/pd_download.png)

_**Note:** Pixiedust currently works only on a Python Notebook hosted on IBM Bluemix._

