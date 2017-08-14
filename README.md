# PixieDust

[![PyPI version](https://badge.fury.io/py/pixiedust.svg)](https://badge.fury.io/py/pixiedust)
[![Build Status](https://travis-ci.org/ibm-watson-data-lab/pixiedust.svg?branch=master)](https://travis-ci.org/ibm-watson-data-lab/pixiedust)  

PixieDust is a productivity tool for Python or Scala notebooks, which lets a developer encapsulate business logic into something easy for your customers to consume.

## Why you need it

Notebooks are a powerful tool for fast and flexible data analysis. But the learning curve is steep.

Python data science notebooks were first popularized in academia, and there are some formalities to work through before you can get to your analysis. For example, in a Python interactive notebook, a mundane task like creating a simple chart or saving data into a persistence repository requires mastery of complex code like this [matplotlib](http://matplotlib.org/) snippet:

![All this for a chart?](https://developer.ibm.com/wp-content/uploads/sites/85/2016/10/hairymatplotlib.png)<br>
*All this for a chart?*

Once you do create a notebook that provides great data insights, it&#39;s hard to share with business users, who don't want to slog through all that dry, hard-to-read code, much less tweak it and collaborate.

PixieDust to the rescue. 

## What is PixieDust?

PixieDust is an open source helper library that works as an add-on to Jupyter notebooks to improve the user experience of working with data. It also fills a gap for users who have no access to configuration files when a notebook is hosted on the cloud. 

### Use in Python or Scala

PixieDust greatly simplifies working with Python display libraries like matplotlib, but works just as effectively in Scala notebooks too. You no longer have compromise your love of Scala to generate great charts. PixieDust lets you bring robust Python visualization options to your Scala notebooks. Installer and instructions to use Scala with PixieDust are coming soon... 

### Features

PixieDust's current capabilities include:

- **[packageManager](https://ibm-watson-data-lab.github.io/pixiedust/packagemanager.html)** lets you install Spark packages inside a Python notebook. This is something that you can't do today on hosted Jupyter notebooks, which prevents developers from using a large number of spark package add-ons.

- **Visualizations.** One single API called `display()` lets you visualize your Spark object in different ways: table, charts, maps, etc.... This module is designed to be extensible, providing an API that lets anyone easily [contribute a new visualization plugin](https://ibm-watson-data-lab.github.io/pixiedust/writeviz.html). 
   
   This sample visualization plugin uses d3 to show the different flight routes for each airport:

   ![graph map](http://developer.ibm.com/clouddataservices/wp-content/uploads/sites/47/2016/07/pd_graphmap.png)
- **Embedded apps.** Let nonprogrammers actively use notebooks. Transform a hard-to-read notebook into a polished graphic app for business users. Check out these preliminary sample apps: 

   - An app can feature embedded forms and responses, [flightpredict](https://github.com/ibm-watson-data-lab/simple-data-pipe-connector-flightstats/tree/master/pixiedust_flightpredict), which lets users enter flight details to see the likelihood of landing on-time.
   - Or present a sophisticated workflow, like our [twitter demo](https://github.com/ibm-watson-data-lab/pixiedust_incubator/tree/master/twitterdemo), which delivers a real-time feed of tweets, trending hashtags, and aggregated sentiment charts with Watson Tone Analyzer. 

- **Extensibility.** Create your own visualizations or apps using the PixieDust extensibility APIs. If you know html and css, you can write and deliver amazing graphics without forcing notebook users to type one line of code. Use the shape of the data to control when PixieDust shows your visualization in a menu.

- **Export.** Notebook users can download data to .csv, HTML, JSON, etc. locally on your laptop or into a variety of back-end data sources, like Cloudant, dashDB, GraphDB, etc...

   ![save as options](http://developer.ibm.com/clouddataservices/wp-content/uploads/sites/47/2016/07/pd_download.png)
- **Scala Bridge.** Use Scala directly in your Python notebook. Variables are automatically transfered from Python to Scala and vice-versa.   [Learn more](https://ibm-watson-data-lab.github.io/pixiedust/scalabridge.html).

  > **Or start in a Scala notebook.** As mentioned, all these PixieDust features work not only in Python, but in Scala too. So if you prefer Scala, you'll soon be able to start there and use PixieDust to insert sophisticated Python graphic options within your Scala notebook. Instructions coming soon.

- **Spark progress monitor.** Track the status of your Spark job. No more waiting in the dark. Notebook users can now see how a cell's code is running behind the scenes.

Watch this video to see PixieDust in action: 

[![about PixieDust](https://img.youtube.com/vi/FoOHFlkCaXI/0.jpg)](https://www.youtube.com/watch?v=FoOHFlkCaXI) 


## Usage

You can use PixieDust locally or online within IBM's Data Science Experience (DSX). 

### Use online

To use PixieDust online
* Sign up for a free trial on IBM's [Data Science Experience](http://datascience.ibm.com/)
* [Create a new notebook from URL](http://datascience.ibm.com/docs/content/analyze-data/creating-notebooks.html) using this template and learn the basics

  `https://github.com/ibm-watson-data-lab/pixiedust/blob/master/notebook/DSX/Welcome%20to%20PixieDust.ipynb` 
  
* [Review the documentation](https://ibm-watson-data-lab.github.io/pixiedust/use.html)  

### Use locally

* Pixiedust supports
 - **Spark 1.6** or **2.0** 
 - **Python 2.7** or **3.5** 

* [Install and configure PixieDust and its prerequisites](https://ibm-watson-data-lab.github.io/pixiedust/install.html) 

* [Explore how to use PixieDust](https://ibm-watson-data-lab.github.io/pixiedust/use.html)


### Sample notebooks
Wherever you prefer to work, try out the following sample notebooks:
 - [Welcome to PixieDust](https://github.com/ibm-watson-data-lab/pixiedust/blob/master/notebook/DSX/Welcome%20to%20PixieDust.ipynb) The ultimate notebook to get started with PixieDust.
 - [Intro to PixieDust](https://github.com/ibm-watson-data-lab/pixiedust/blob/master/notebook/Intro%20to%20PixieDust.ipynb).  Uses PackageManager to install GraphFrames, generates a dataframe from a simple data set, and lets you try the display() API. See also: [Intro to PixieDust for Spark 2.0](https://github.com/ibm-watson-data-lab/pixiedust/blob/master/notebook/Intro%20to%20PixieDust%20Spark%202.0.ipynb)
 - [Mapping Intro](https://github.com/ibm-watson-data-lab/pixiedust/blob/master/notebook/mapping_intro.ipynb) lets you load sample data sets, explore display() API features, including maps.

### Tutorials

 - [Discover hidden Facebook usage insights](https://developer.ibm.com/code/journey/discover-hidden-facebook-usage-insights/)
 - [FlightPredict II: The Sequel](https://medium.com/ibm-watson-data-lab/flightpredict-ii-the-sequel-fb613afd6e91) shows how to predict flight delays with PixieDust. Includes an embedded app
 - [Sentiment Analysis of Twitter Hashtags with Spark](https://medium.com/ibm-watson-data-lab/real-time-sentiment-analysis-of-twitter-hashtags-with-spark-7ee6ca5c1585#.gbqjjf3ef) revisits a spark streaming app this time using PixieDust and Jupyter. Includes an embedded app.

## Contribute

_**Note:** PixieDust currently supports Spark DataFrames, Spark GraphFrames and Pandas DataFrames, with more to come. If you can't wait, write your own today and contribute it back._

Read [how to contribute](https://ibm-watson-data-lab.github.io/pixiedust/contribute.html) for details on our code of conduct and instructions for submitting pull requests to us. 

### Developer Guide

Dive into the [PixieDust developer docs](https://ibm-watson-data-lab.github.io/pixiedust/) and learn how to build your own custom visualization or embedded app. You can also pitch in and contribute an enhancement to PixieDust's core features. 

We can't wait to see what you build.

## License

**Apache License, Version 2.0**. 

For details and all the legalese, [read LICENSE](https://github.com/ibm-watson-data-lab/pixiedust/blob/master/LICENSE).
