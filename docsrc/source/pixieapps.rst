PixieApps
=========

**What are PixieApps?**

PixieApps are Python classes used to write UI elements for your analytics, and they run directly in a Jupyter notebook.

PixieApps are designed to be easy to build. Mostly, you'll only need to write HTML and CSS with some custom attributes, along with some Python for the business logic. Except in rare cases, you won't have to write JavaScript. The PixieDust JS runtime will automatically listen to key events and manage transactions to the Jupyter kernel appropriately.

.. image:: _images/pixieapp-chart.png

At its core, a PixieApp is composed of views (in the `MVC <https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller>`_ sense), which are HTML fragments. Each view has a route definition (a set of key/value pairs) that the PixieApp framework uses to decide when to dispatch the current transaction based on current app state. You'll find more details in the sub-topics here.

.. toctree::
   :maxdepth: 2

   hello-world-pixieapp
   reference-pixieapp
   html-attributes-pixieapp
   custom-elements-pixieapp
   dynamic-values-pixieapp
   create-widget-pixieapp
   hello-world-data-pixieapp