# PixieDust

[![PyPI version](https://badge.fury.io/py/pixiedust.svg)](https://badge.fury.io/py/pixiedust)
[![Build Status](https://travis-ci.org/ibm-cds-labs/pixiedust.svg?branch=master)](https://travis-ci.org/ibm-cds-labs/pixiedust)  

PixieDust is a productivity tool for python notebooks, which lets a developer encapsulate business logic into something easy for your customers to consume.

##Why you need it

Python notebooks are a powerful tool for fast and flexible data analysis. But the learning curve is steep.

Data science notebooks were first popularized in academia, and there are some formalities to work through before you can get to your analysis. For example, in a Python interactive notebook, a mundane task like creating a simple chart or saving data into a persistence repository requires mastery of complex code like this [matplotlib](http://matplotlib.org/) snippet:

![All this for a chart?](https://developer.ibm.com/wp-content/uploads/sites/85/2016/10/hairymatplotlib.png)<br>
*All this for a chart?*

Once you do create a notebook that provides great data insights, it&#39;s hard to share with business users, who don't want to slog through all that dry, hard-to-read code, much less tweak it and collaborate.

PixieDust to the rescue. 

##What is PixieDust?

PixieDust is an open source Python helper library that works as an add-on to Jupyter notebooks to improve the user experience of working with data. It also fills a gap for users who have no access to configuration files when a notebook is hosted on the cloud.

###Features

PixieDust's current capabilities include:

- **[packageManager](https://ibm-cds-labs.github.io/pixiedust/packagemanager.html)** lets you install spark packages inside a python notebook. This is something that you can't do today on hosted Jupyter notebooks, which prevents developers from using a large number of spark package add-ons.

- **Visualizations.** One single API called `display()` lets you visualize your spark object in different ways: table, charts, maps, etc.... This module is designed to be extensible, providing an API that lets anyone easily [contribute a new visualization plugin](https://ibm-cds-labs.github.io/pixiedust/writeviz.html). 
   
   This sample visualization plugin uses d3 to show the different flight routes for each airport:

   ![graph map](http://developer.ibm.com/clouddataservices/wp-content/uploads/sites/47/2016/07/pd_graphmap.png)
- **Embedded apps.** Let nonprogrammers actively use notebooks. Transform a hard-to-read notebook into a polished graphic app for business users. Check out these preliminary sample apps: 

   - An app can feature embedded forms and responses, [flightpredict](https://github.com/ibm-cds-labs/simple-data-pipe-connector-flightstats/tree/master/pixiedust_flightpredict), which lets users enter flight details to see the likelihood of landing on-time.
   - Or present a sophisticated workflow, like our [twitter demo](https://github.com/ibm-cds-labs/pixiedust_incubator/tree/master/twitterdemo), which delivers a real-time feed of tweets, trending hashtags, and aggregated sentiment charts with Watson Tone Analyzer. 

- **Extensibility.** Create your own visualizations or apps using the pixiedust extensibility APIs. If you know html and css, you can write and deliver amazing graphics without forcing notebook users to type one line of code. Use the shape of the data to control when Pixiedust shows your visualization in a menu.

- **Export.** Notebook users can download data to .csv, html, json, etc. locally on your laptop or into a variety of back-end data sources, like Cloudant, dashDB, GraphDB, etc...

   ![save as options](http://developer.ibm.com/clouddataservices/wp-content/uploads/sites/47/2016/07/pd_download.png)
- **Scala Bridge.** Use scala directly in your Python notebook. Variables are automatically transfered from Python to Scala and vice-versa. 

- **Spark progress monitor.** Track the status of your Spark job. No more waiting in the dark. Notebook users can now see how a cell's code is running behind the scenes.

>**What about Scala?** This is a Python library but you can use it in a Scala notebook too. [Learn more](https://ibm-cds-labs.github.io/pixiedust/scalabridge.html).  

Check out this detailed presentation of PixieDust: 

[![about PixieDust](https://img.youtube.com/vi/JcMefQ_o9oU/0.jpg)](https://www.youtube.com/watch?v=JcMefQ_o9oU) 

###Demo

Try a demo notebook. PixieDust is built-in to IBM's [Data Science Experience](http://datascience.ibm.com/). For a quick look at PixieDust, you can sign up for a free trial there, and create a new notebook from URL using this sample: `https://github.com/ibm-cds-labs/pixiedust/raw/master/notebook/Intro%20to%20PixieDust.ipynb` 

To see an embedded app in action, run the following tutorial in Data Science Experience: [FlightPredict II: The Sequel](https://medium.com/ibm-watson-data-lab/flightpredict-ii-the-sequel-fb613afd6e91), which shows how to predict flight delays with PixieDust.

##Get started

Get PixieDust up and running on your local machine for development and testing. 

###Requirements

You'll get the following as part of PixieDust installation:


- **Spark 1.6** or **2.0** 
- **Python 2.7** or **3.5** 
- **PySpark.** The Python API for Spark. Many features of PixieDust (but not all) are Spark-related.  So Spark and the PySpark package are required.


_**Note:** PixieDust currently supports Spark DataFrames, Spark GraphFrames and Pandas DataFrames, with more to come. If you can't wait, write your own today and contribute it back._

###Install

[Install and configure PixieDust](https://ibm-cds-labs.github.io/pixiedust/install.html) to see how it works and to start exploring your development options.

##Contribute

Read [how to contribute](https://ibm-cds-labs.github.io/pixiedust/contribute.html) for details on our code of conduct and instructions for submitting pull requests to us. 

###Developer Guide

Dive into the [PixieDust developer docs](https://ibm-cds-labs.github.io/pixiedust/) and learn how to build your own custom visualization or embedded app. You can also pitch in and contribute an enhancement to PixieDust's core features. 

We can't wait to see what you build.

##License
details to follow...
