Install PixieDust
=================
PixieDust is a Python library for use in Jupyter notebooks. 
PixieDust is bundled as a Python package and can be installed using pip.
To install and configure PixieDust please follow the instructions below:

Prerequisites
=============
In order to use PixieDust inside your Jupyter notebooks you will, of course, need Jupyter.
The easiest way to install Jupyter is by installing Anaconda.
Anaconda is a Data Science platform which consists of a Python distribution and collection of open source packages well suited for scientific computing.
Anaconda includes Python, pip, pandas, numpy, matpoltlib, and other libraries required to run PixieDust effectively.

To install Anaconda go to `<https://www.continuum.io/downloads>`_ and follow the instructions.

Note: PixieDust supports both Python 2.7 and Python 3.5.

Install PixieDust
=================
Once you've installed Anaconda run the following commands in your Terminal or command-line interface to ensure your environment is configured properly:
::

    pip  --version
    jupyter --version

You can install the PixieDust library from source or from PyPI.
If you plan on contributing to PixieDust it is recommended that you install from source.

Install from Source
-------------------

To install PixieDust from source first clone the PixieDust repo on GitHub:
::

    git clone https://github.com/ibm-cds-labs/pixiedust

Next, run `pip` with the `-e` flag to install the PixieDust from the local directory:
::

    pip install -e ./pixiedust

Install from PyPI
-----------------

Alternatively, you can install the last version of PixieDust from PyPI using pip:
::

    pip install --user --upgrade pixiedust

Jupyter Kernels
===============

In order to use PixieDust inside Jupyter you must install a new Jupyter kernel.
Kernels are processes that run interactive code from your Jupyter notebook.
PixieDust uses pyspark; a Python binding for Apache Spark.
PixieDust includes a command-line utility for installing new kernels that use pyspark.
The command-line utility will walk you through the steps of configuring your kernel as well as installing Apache Spark and Scala (required if you want to run Scala code from within your Python notebook).

Install a Jupyter Kernel
------------------------

From a Terminal or command-line interface run the following:
::

    jupyter pixiedust install

The install will first ask you to set a path for `PIXIEDUST_HOME`.
This is a directory that PixieDust will use to keep track of your PixieDust install, including any libraries you install from PixieDust.
You may choose to keep the default path, or select a new one:
::

    Step 1: PIXIEDUST_HOME: /Users/USERNAME/pixiedust
        Keep y/n [y]? y

After you have configured PIXIEDUST_HOME you will be prompted to specify the location of your Apache Spark install.
If you do not have Apach Spark installed the installer will download one for you:
::

    Step 2: Please enter a SPARK_HOME location: /Users/USERNAME/spark
    Directory /Users/USERNAME/spark does not contain a valid SPARK install
        Download Spark y/n [y]? y

If you choose to download Apache Spark the installer will prompt you for the version, download it, and configure your SPARK_HOME accordingly:
::

    What version would you like to download? 1.6.3, 2.0.2, 2.1.0 [2.1.0]: 2.1.0
    SPARK_HOME will be set to /Users/USERNAME/spark/spark-2.1.0-bin-hadoop2.7
    Downloading Spark 2.1.0
    Extracting Spark 2.1.0 to /Users/USERNAME/spark


Next, the installer will prompt you for the location of Scala.
If you do not have Scala installed, or you do not have the version of Scala supported by your Apache Spark install, the installer will download the appropriate version of Scala for you.
::

    Step 3: Please enter a SCALA_HOME location: /Users/USERNAME/scala
    Directory /Users/USERNAME/scala does not contain a valid SCALA install
        Download Scala y/n [y]? y
    SCALA_HOME will be set to /Users/USERNAME/scala/scala-2.11.8
    Downloading Scala 2.11
    Extracting Scala 2.11 to /Users/USERNAME/scala

Finally, the installer will ask you for a name for the kernel.
::

    Step 4: Kernel Name: Python with Pixiedust (Spark 2.1)
        Keep y/n [y]? y

That's it! You can now run a Jupyter notebook using Apache Spark and PixieDust.

Note: You can have more than one kernel for PixieDust.
If you would like to install a new kernel with a different version of Spark just re-run the installer and choose the appropriate version.

List Existing Kernels
---------------------

You can list the existing Jupyter kernels from the command-line by running the following command:
::

    jupyter pixiedust list

The output will look similar to the following:
::

    Available kernels:
        pythonwithpixiedustspark20    /Users/USERNAME/Library/Jupyter/kernels/pythonwithpixiedustspark20
        pythonwithpixiedustspark21    /Users/USERNAME/Library/Jupyter/kernels/pythonwithpixiedustspark21
