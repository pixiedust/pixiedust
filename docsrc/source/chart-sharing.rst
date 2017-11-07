Chart Sharing
=============

Starting with PixieDust 1.1.1, the PixieGateway server now supports sharing of charts created with the display() function, effectively turning them into standalone web pages. No coding necessary.

Simply use the interactive PixieDust display() function from within a Jupyter Notebook to build your chart, click on the Share button, add an optional description. You'll get a URL. Visitors to your page will see the chart without needing to run a Jupyter Notebook. All they need is a web browser.

Chart Sharing in Action
-----------------------

Using ``display()`` to create a chart, you’ll now see a **Share** button next to “Options”:

.. image:: _images/pixiegateway-chart-sharing.png

The Share dialog will ask for the following information:

1. **PixieGateway server:** If you don’t have one, `see the docs <install-pixiegateway.html>`_ for instructions on how to set one up.

2. **Description:** Optional free-form text explaining what the chart is about. It will be added to the standalone webpage.

.. image:: _images\pixiegateway-share-chart.png

Click **Share**, and if all goes well, you should get a URL for your chart webpage that is ready to share:

.. image:: _images\pixiegateway-chart-url.png
   :width: 800 px

You can copy the URL or click on the link to go directly to the page:

.. image:: _images\pixiegateway-published-chart.png