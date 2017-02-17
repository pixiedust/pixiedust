Load Data
========================

Sample Data Sets
----------------

PixieDust comes with sample data. To start playing with the display() API and other PixieDust features, load and then visualize one of our many sample data sets.

To call the list of data sets, run the following command in your notebook:

   ::


     pixiedust.sampleData()


You get a list of the data sets included with PixieDust.


.. image:: _images/sample_data_sets.png


To create a pySpark DataFrame for one of the samples, just enter its number in the following command. For example, to load Set 6, Million Dollar Home sales, run the command:

   ::


     home_df = pixiedust.sampleData(6)

