Write a new PixieDust Visualization
===================================

Create your own visualizations or apps using the pixiedust extensibility APIs. If you know html and css, you can write and deliver amazing graphics without forcing notebook users to type one line of code. Use the shape of the data to control when Pixiedust shows your visualization in a menu.

When a notebook user invokes ``display()``, PixieDust provides a chrome that include a toolbar of menus. Each menu is a way to visualize or perform action on the data. 

PixieDust framework builds that menu based on introspecting the data itself and associating it with components that the developer declares can process that data.  PixieDust comes with a set of visualizations and actions out-of-the-box, but you can easily add your own custom plugin. 

QuickStart
----------

To get started fast, try our generator, which lets you create a sample visualization by answering a few prompts in Terminal or other command line app. 

1. In Terminal or other command-line shell, navigate to the directory where you want to create the new project. This can be anywhere you choose.

2. Enter and run:

  ``jupyter pixiedust generate``

3. Respond to the questions/prompts to complete setup. Here's the entire exchange including the command you'll run in Step 4:

   .. image:: _images/generate_vis.png 

4. Install your new visualization.

   If you're not already there, cd into your project directory and run the following command: 

   ``pip install -e .``

5. Go to your notebook, and restart the kernel.

6. Run the command ``import pixiedust`` 

7. Run the command ``import Sampleviz``  (or whatever you named your project)

8. Then load some data and run the display() command on it. 

9. In the charts dropdown, choose a chart you specified that the renderer can display.

10. Click the **Renderer** dropdown. 

   You see your new visualization menu item! Here's one named **Sampleviz**:

   .. image:: _images/sample_viz_menu.png

Explore the code in your new project directory. We've commented in some guidance that should help you understand what you're looking at.

Code walk-through: Display a DataFrame as a table
--------------------------------------------------------

Here's a run-down of what goes into a PixieDust visualization:

Hook into the display menu
**************************

First, for a user to invoke a graph or visualization, it must appear on the PixieDust menu.

class TableDisplayMeta
######################

The first thing you'll want to do is get your tool presented in the menu. Since you're building a tool to display a DataFrame as an HTML table, look at ``display/table/__init__.py``:

   ::

    @PixiedustDisplay(isDefault=True)
    class TableDisplayMeta(DisplayHandlerMeta):
      @addId
      def getMenuInfo(self,entity, dataHandler):
          if dataFrameMisc.isPySparkDataFrame(entity) or dataFrameMisc.isPandasDataFrame(entity):
              return [
                  {"categoryId": "Table", "title": "DataFrame Table", "icon": "fa-table", "id": "dataframe"}
              ]
          elif dataFrameMisc.fqName(entity) == "graphframes.graphframe.GraphFrame":
              return [
                  {"categoryId": "Table", "title": "Graph Vertices", "icon": "fa-location-arrow", "id":"vertices"},
                  {"categoryId": "Table", "title": "Graph Edges", "icon": "fa-link", "id":"edges"}
             ]
          else:
              return []
      def newDisplayHandler(self,options,entity):
          return TableDisplay(options,entity)


Here you see that class ``TableDisplayMeta`` does 2 things. In the method ``getMenuInfo``, it decides what menus to load, depending on the type of entity passed. In the method ``newDisplayHandler``, it does the actual data processing.

def getMenuInfo
###############

In the ``getMenuInfo`` method of class ``TableDisplayMeta`` you check for the type of the entity. Pixiedust currently supports ``GraphFrame`` and ``PySparkDataFrame`` (currently only 2-dimensional matrix Pandas DataFrames are supported, so you can consider them to be the same as ``PySparkDataFrame`` for the purposes of Pixiedust development). 

If it's a Pandas or PySpark DataFrame, return an array of menu definition objects. A menu definition object consists of 4 properties:

1. ``categoryId``: a unique string that identifies the menu "category" or group
2. ``title``: an arbitrary string that describes the menu
3. ``icon``: the name of a fontawesome icon, or a URL for an image
4. ``id``: a unique string that identifies your tool

Pixiedust only has one option for displaying a DataFrame as a table, so you return a single menu object in the array. 

def newDisplayHandler
#####################

The other method you must implement is ``newDisplayHandler``, which is called when the menu item is selected. This is where the DataFrame is actually processed. In this case, return a new ``TableDisplay`` object, which does all the heavy lifting that we'll talk about next. 

Data Processing
***************

 The ``TableDisplay`` class is defined in ``display/table/display.py``. You can `see the code on GitHub <https://gist.github.com/rajrsingh/67e45a1c0ecc64207a189501d9559ea5>`_.

   ::

     class TableDisplay(Display):
         def doRender(self, handlerId):
             entity=self.entity       
             if dataFrameMisc.fqName(entity) == "graphframes.graphframe.GraphFrame":
                 if handlerId == "edges":
                     entity=entity.edges
                 else:
                     entity=entity.vertices
             if dataFrameMisc.isPySparkDataFrame(entity) or dataFrameMisc.isPandasDataFrame(entity):
                 self._addHTMLTemplate('dataframeTable.html', entity=PandasDataFrameAdapter(entity))
                 return
            
             self._addHTML("""
                 <b>Unable to display object</b>
             """
             )


This class must implement one method, ``doRender``, which is called with a reference to ``self`` and a ``handlerId``. In the case of DataFrame display, the ``handlerId`` is unused, so you only need to check for one  DataFrameentity type. You can display it using a `Jinja2 <http://jinja.pocoo.org/>`_ HTML template. 

HTML rendering with Jinja2
**************************

This line of code: 

``self._addHTMLTemplate('dataframeTable.html', entity=PandasDataFrameAdapter(entity))``

is the key to rendering our data. ``dataframeTable.html`` (by default found in the templates directory in the same directory as the calling file) is a Jinja2 template consisting of CSS styles, HTML and data processing language. You should study this file carefully `here <https://gist.github.com/rajrsingh/8bdfe8ac7b87f442640f85292b1aab82>`_, but the key lines are:

1. ``{% set rows = entity.take(100) %}``: get the first 100 lines of the DataFrame and assign to variable ``rows``
2. ``{% for field in entity.getFields() %}``: loop over the fields and display each as a ``<th>``
3. ``{% for row in rows %}``: loop over the rows and display each as a ``<tr>``

Also note the ``<script>`` tag at the end of the file. This is where you can do some nifty extras like scrolling while keeping the table header in a fixed position and client-side search.

Build your own table display plugin
---------------------------------

Now that you've seen how Pixiedust works, let's build a very simple second table display tool. You'll need to do 3 things:

1. Add a menu item and hook it to your code
3. Transform the DataFrame into something a web browser can display (HTML in our case, but it could be SVG, a PDF or something more exotic) using Jinja2 HTML templating

Add a menu item and hook it to your code
****************************************

Have Pixiedust recognize your new menu item code by adding this line in the imports of ``__init__.py`` (in the directory ``display/table``):

``from .SimpleDisplayMeta import SimpleDisplayMeta``

Then create the file SimpleDisplayMeta.py and enter this code: 


   ::

     from .SimpleDisplay import SimpleDisplay
     from ..display import *
     import pixiedust.utils.dataFrameMisc as dataFrameMisc

     @PixiedustDisplay()
     class SimpleDisplayMeta(DisplayHandlerMeta):
        @addId
        def getMenuInfo(self,entity,dataHandler):
             if dataFrameMisc.isPySparkDataFrame(entity) or dataFrameMisc.isPandasDataFrame(entity):   
                return [
                    {"categoryId": "Table", "title": "Simple Table", "icon": "fa-table", "id": "simpleTest"}
                ]
             else:
           return []
        def newDisplayHandler(self,options,entity):
            return SimpleDisplay(options,entity)


As described earlier, the method ``getMenuInfo`` provides the hook to add a menu item to the user interface. You specify "Table" as the ``categoryID`` to add this tool to the existing Table menu. Give it any `title` and ``icon`` you want. And finally, give it a unique id, such as "simpleTest". 

The ``newDisplayHandler`` method specifies the code used to do the data processing work. That looks like this:

DataFrame => HTML
*****************

Create the file SimpleDisplay.py in the directory `display/table`, and enter this code:


   ::

     from ..display import *
     from pyspark.sql import DataFrame
     from pixiedust.utils.dataFrameAdapter import *
     import pixiedust.utils.dataFrameMisc as dataFrameMisc
    
     class SimpleDisplay(Display):
         def doRender(self, handlerId):
             entity=self.entity
             if dataFrameMisc.isPySparkDataFrame(entity) or dataFrameMisc.isPandasDataFrame(entity):
                 self._addHTMLTemplate('simpleTable.html', entity=PandasDataFrameAdapter(entity))
                 return
            
             self._addHTML("""
                 <b>Unable to display object</b>
             """
             )


All you're really doing here is defining a mechanism to call the right Jinja template -- ``simpleTable.html`` found in the ``templates`` directory -- for processing the data. Once you're working on the template, the sky's the limit for what you can do. But just to finish out this example, here's some extremely simple code you can add there:


   ::

     <table class="table table-striped">
        <thead>                 
            {%for field in entity.schema.fields%}
            <th>{{field.name}}</th>
            {%endfor%}
        </thead>
        <tbody>
            {%for row in entity.take(100)%}
            <tr>
                {%for field in entity.schema.fields%}
                <td>{{row[field.name]}}</td>
                {%endfor%}
            </tr>
            {%endfor%}
        </tbody>
     </table>


What you get
############

Now that the code is complete. Let's update Pixiedust in our notebook and see the results. Shut down your Jupyter environment, run the below command from your terminal, and restart Jupyter to get the new code. 

``pip install --user -e <your directory path to pixiedust code>``

You should now see something resembling the screenshot below. The table menu is now a dropdown with two options, **DataFrame Table** and your new **Simple Table**. Choosing **Simple Table** displays the data using the template you defined in simpleTable.html! 

.. container:: 

.. raw:: html

     <img src="http://developer.ibm.com/clouddataservices/wp-content/uploads/sites/85/2017/01/pixiedustnewtableoption.png" width="615">




.. note::  PixieDust provides a higher level framework built on top of ``display()`` api that lets you contribute more tightly to the chart menus. When you use the renderer api you contribute to the list renderers that can display a particular type of chart. For example, let notebook users choose Mapbox to display a map. At the lowest level you can create only a visualization and don’t need to specify a renderer. But if you're interested in learning more, read how to `build a renderer <renderer.html>`_.


.. image:: _images/draft-watermark.png