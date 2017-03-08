Install PixieDust
=================
PixieDust is a Python library for use in Jupyter notebooks. To use PixieDust in your local environment, you must install it.
PixieDust is bundled as a Python package and can be installed using pip.
To install and configure PixieDust complete the following steps:

Prerequisites
-------------
In order to use PixieDust inside your Jupyter notebooks you will, of course, need Jupyter.
The easiest way to install Jupyter is by installing Anaconda.
Anaconda is a Data Science platform which consists of a Python distribution and collection of open source packages well-suited for scientific computing.
Anaconda includes Python, pip, pandas, numpy, matpoltlib, and other libraries required to run PixieDust effectively.

To install Anaconda go to `<https://www.continuum.io/downloads>`_ and follow the instructions.

.. note:: PixieDust supports both Python 2.7 and Python 3.5.

Install PixieDust
-----------------
Once you've installed Anaconda run the following commands in your Terminal or command-line interface to ensure your environment is configured properly:
::

    pip  --version
    jupyter --version

You can install the PixieDust library from source or from PyPI.
If you plan on contributing to PixieDust we recommended that you install from source.

- **Install from Source**

   To install PixieDust from source, first clone the PixieDust repo on GitHub:
   ::

       git clone https://github.com/ibm-cds-labs/pixiedust

   Next, run `pip` with the `-e` flag to install the PixieDust from the local directory:
   ::

       pip install -e ./pixiedust

- **Install from PyPI**

   Alternatively, you can install the last version of PixieDust from PyPI using pip:
   ::

       pip install pixiedust

.. note:: Do not include ``--user`` in your pip install command. Doing so installs the Jupyter PixieDust command in the wrong directory, and you won't be able to follow the rest of the steps on this page.

Jupyter Kernels
---------------

In order to use PixieDust inside Jupyter you must install a new Jupyter kernel.
Kernels are processes that run interactive code from your Jupyter notebook.
PixieDust uses pyspark; a Python binding for Apache Spark.
PixieDust includes a command-line utility for installing new kernels that use pyspark.
The command-line utility walks you through the steps of configuring your kernel as well as installing Apache Spark and Scala (required if you want to run Scala code from within your Python notebook).

Install a Jupyter Kernel
************************

From a Terminal or command-line interface run the following:
::

    jupyter pixiedust install

The install will first ask you to set a path for `PIXIEDUST_HOME`.
This is a directory that PixieDust will use to keep track of your PixieDust install, including any libraries you install from PixieDust.
You may choose to keep the default path, or select a new one:
::

    Step 1: PIXIEDUST_HOME: /Users/USERNAME/pixiedust
        Keep y/n [y]? y

After you have configured PIXIEDUST_HOME you are prompted to specify the location of your Apache Spark install.
If you do not have Apache Spark installed, the installer downloads it for you:
::

    Step 2: Please enter a SPARK_HOME location: /Users/USERNAME/spark
    Directory /Users/USERNAME/spark does not contain a valid SPARK install
        Download Spark y/n [y]? y

If you choose to download Apache Spark, the installer prompts you for the version. Download it, and configure your SPARK_HOME accordingly:
::

    What version would you like to download? 1.6.3, 2.0.2, 2.1.0 [2.1.0]: 2.1.0
    SPARK_HOME will be set to /Users/USERNAME/spark/spark-2.1.0-bin-hadoop2.7
    Downloading Spark 2.1.0
    Extracting Spark 2.1.0 to /Users/USERNAME/spark

*Tip: If you're using Spark 1.6, and you want to work with PixieDust's sample data (recommended!), manually add the following package when you run your notebook. (You need run these commands only once.):*

   ::

      pixiedust.installPackage("com.databricks:spark-csv_2.10:1.5.0")
      pixiedust.installPackage("org.apache.commons:commons-csv:0")

Next, the installer prompts you for the location of Scala.
If you do not have Scala installed, or you do not have the version of Scala supported by your Apache Spark install, the installer downloads the appropriate version of Scala for you.
::

    Step 3: Please enter a SCALA_HOME location: /Users/USERNAME/scala
    Directory /Users/USERNAME/scala does not contain a valid SCALA install
        Download Scala y/n [y]? y
    SCALA_HOME will be set to /Users/USERNAME/scala/scala-2.11.8
    Downloading Scala 2.11
    Extracting Scala 2.11 to /Users/USERNAME/scala

Finally, the installer asks you for a name for the kernel.
::

    Step 4: Kernel Name: Python with Pixiedust (Spark 2.1)
        Keep y/n [y]? y

That's it! You can now run a Jupyter notebook using Apache Spark and PixieDust.

..note:: You can have more than one kernel for PixieDust. If you want to install a new kernel with a different version of Spark just re-run the installer and choose the appropriate version.

List Existing Kernels
*********************

You can list the existing Jupyter kernels from the command-line by running the following command:
::

    jupyter pixiedust list

The output looks similar to this:
::

    Available kernels:
        pythonwithpixiedustspark20    /Users/USERNAME/Library/Jupyter/kernels/pythonwithpixiedustspark20
        pythonwithpixiedustspark21    /Users/USERNAME/Library/Jupyter/kernels/pythonwithpixiedustspark21

Stash to Cloudant
-----------------

You can export the data to a Cloudant database. A supporting library cloudant-spark jar is required for the export.
This is a manual one-time step that requires a kernel restart. Download cloudant-spark jar file for respective Spark version from
::

    Spark 1.6: https://github.com/cloudant-labs/spark-cloudant/releases/download/v1.6.4/cloudant-spark-v1.6.4-167.jar
    Spark 2.0: https://github.com/cloudant-labs/spark-cloudant/releases/download/v2.0.0/cloudant-spark-v2.0.0-185.jar

Create a directory of your choice for example jars under the home directory.
::

    mkdir jars

Copy the cloudant-spark jar file into the newly created directory.

Locate kernel.json file under the directory listing by running command.
::

    jupyter pixiedust list

Edit kernel.json file and update the variable PYSPARK_SUBMIT_ARGS under env by adding --jars <local_home_directory>/jars/cloudant-spark.jar.
::

    "PYSPARK_SUBMIT_ARGS": "--jars /Users/USERNAME/jars/cloudant-spark-v1.6.4-167.jar ....


Try It Out!
-----------

The PixieDust GitHub repo includes a sample notebook (*Intro to PixieDust.ipynb*) that you can use to try out your PixieDust install.
If you installed PixieDust from source you can find this notebook in *pixiedust/notebook*.
Otherwise, you can download the notebook `here <https://github.com/ibm-cds-labs/pixiedust/blob/master/notebook/Intro%20to%20PixieDust.ipynb>`_

After you have downloaded the *Intro to PixieDust.ipynb* notebook run the following command:
::

    jupyter notebook directory/containing/notebook

This should automatically open a web browser that looks shows you this:

.. container:: 

.. raw:: html

     <img src="_images/install-notebook1.png" width="615">

Click **Intro to PixieDust.ipynb**. You may be prompted to select a kernel. Select the kernel you created using the installer.
Alternatively, click **Kernel > Change Kernel** from the menu to select the appropriate kernel:

.. container:: 

.. raw:: html

     <img src="_images/install-notebook2.png" width="615">

This notebook shows you how to import the PixieDust library and run a handful of PixieDust features.
