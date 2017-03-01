Download Data 
========================

PixieDust lets you download the data from your notebook. If you've been playing with some charts, you can also save and download in SVG format.

Save data to a file
-------------------

You can save a data set to a number of different file formats, including CSV, JSON, XML, and more. You do so within the user interface controls that the display API generates. `Read how to run and work with display() <displayapi.html>`_. 

1. Above the table and charts display, click the Download dropdown arrow. You see the following menu: 

   .. image:: _images/downloadfile.png

2. Choose **Download as File**
   Choose the format you want, and specify the number of records to download.

   .. image:: _images/save_as.png

3. Click **OK**.

Export data to Cloudant :sup:`BETA`
--------------------------------------

PixieDust also lets you save directly to a Cloudant database. 

1. Above the table and charts display, click the Download dropdown arrow. You see the following menu: 

   .. image:: _images/downloadfile.png

2. Choose **Stash to Cloudant**.

3. To the right of the **Cloudant Connection** field, click the + plus button. 

4. Enter your Cloudant database credentials and click **OK**.

.. note:: If you get an error that a library is missing, you may need to `install the cloudant-spark library <https://github.com/ibm-cds-labs/pixiedust/blob/plotting-tools/docsrc/source/install.rst#stash-to-cloudant>`_. If you get a **Too many requests** error, you are on the Cloudant Lite plan. The only way to raise limits, is to upgrade your Cloudant plan.

Save a chart or map in SVG format
---------------------------------

If you've created a sweet chart that you want to save, click the **Download SVG** button.  
