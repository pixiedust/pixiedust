Use Scala in a Python Notebook
==============================


Introduction
------------

Python has a rich ecosystem of modules including plotting with Matplotlib, data structure and analysis with Pandas, Machine Learning or Natural Language Processing. However, data scientists working with Spark may occasionaly need to call out one of the hundreds of libraries available on `spark-packages.org <https://spark-packages.org/>`_ which are written in Scala or Java. Unfortunately, Jupyter Python notebooks do not currently provide a way to call out scala code. As a result, a typical workaround is to first use a Scala notebook to run the Scala code, persist the output somewhere like a Hadoop Distributed File System, create another Python notebook, and re-load the data. This is obviously inefficent and awkward. 

PixieDust provides a solution to this problem by letting users directly write and run scala code in its own cell. It also lets variables be shared between Python and Scala and vice-versa.

Using Scala cell magic
----------------------

After importing the PixieDust module, users can simply use the %%scala magic to write Scala code and run the cell as any other normal cell. Any compilation error will be reported in the cell output.  
The following example shows how to run the `Watson sentiment sample app <https://developer.ibm.com/clouddataservices/sentiment-analysis-of-twitter-hashtags/>`_ written in Scala:  

First install the jar into the Python kernel:

   ::

     import pixiedust
     pixiedust.installPackage("https://github.com/ibm-cds-labs/spark.samples/raw/master/dist/streaming-twitter-assembly-1.6.jar")


You can now run the Scala code that uses Spark Streaming to fetch tweets:  

   ::

     %%scala
     val demo = com.ibm.cds.spark.samples.StreamingTwitter
     demo.setConfig("twitter4j.oauth.consumerKey","XXXX")
     demo.setConfig("twitter4j.oauth.consumerSecret","XXXX")
     demo.setConfig("twitter4j.oauth.accessToken","XXXX")
     demo.setConfig("twitter4j.oauth.accessTokenSecret","XXXX")
     demo.setConfig("watson.tone.url","https://gateway.watsonplatform.net/tone-analyzer/api")
     demo.setConfig("watson.tone.password","XXXX")
     demo.setConfig("watson.tone.username","XXXX")

     import org.apache.spark.streaming._
     demo.startTwitterStreaming(sc, Seconds(30))


Variable transfer
-----------------

Every variable defined within Python are accessible in Scala.
For example:  

   ::

     #define variables in python
     var1="Hello"
     var2=200


You can then access these variables in Scala  

   ::

     println(var1)
     println(var2 + 10)


Likewise, you can transfer variables defined in Scala by prefixing them with __ (2 underscores). The following example shows how to access the tweets into a dataframe and transfer them into the python shell namespace:

   ::

     %%scala
     val demo = com.ibm.cds.spark.samples.StreamingTwitter 
     val (__sqlContext, __df) = demo.createTwitterDataFrames(sc)


Then use the __df variable in Python

   ::

     print(__df.count())

