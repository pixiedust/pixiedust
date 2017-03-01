Package Manager
===============

Introduction
------------

You can use the PackageManager component of Pixiedust to install and
uninstall maven packages into your notebook kernel without editing
configuration files. This component is essential when you run
notebooks from a hosted cloud environment and do not have access to the configuration files.

You can use this component in the following ways:

- Install a spark package from spark-packages.org.
- Install from maven search repository.
- Install a jar file directly from an addressable location.
 

Install a spark package
-----------------------

1. Go to `spark-packages.org <https://spark-packages.org/>`_, and search for your package.
2. Click the link for your package and locate the code to run the package in spark-shell, pyspark, or spark-submit. For example, you would retrieve the following line:

   ::

       > $SPARK_HOME/bin/spark-shell --packages graphframes:graphframes:0.1.0-spark1.6

3. Copy the maven ID of the package. A maven ID includes a group ID,
   artifact ID, and version number, each separated by a colon (:). In
   the previous example, the maven ID appears after the packages, such
   as **graphframes:graphframes:0.1.0-spark1.6**.
4. From a Python notebook, enter the following command:

   ::

       import pixiedust
       pixiedust.installPackage("graphframes:graphframes:0.1.0-spark1.6")

   To fetch the latest release, specify 0 as the version. The Pixiedust
   packageManager fetches the latest release in the following example.

   ::

       import pixiedust
       pixiedust.installPackage("graphframes:graphframes:0")

After you successfully issue the import command, the following results
display:

::

    Downloading artifact graphframes:graphframes:0.1.0-spark1.6
    Downloaded 326112 of 326112 bytes (100.00%)
    Downloaded artifact graphframes:graphframes:0.1.0-spark1.6 to /Users/dtaieb/data/libs/graphframes-0.1.0-spark1.6.jar
    Artifact downloaded successfully graphframes:graphframes:0.1.0-spark1.6
    >>>Please restart Kernel to complete installation of the new package
    Successfully added artifact graphframes:graphframes:0.1.0-spark1.6

Notice the line that instructs you to restart the kernel to complete
installation of the new package. This is required only the first time.
Restart the kernel by using the **Kernel/Restart** menu. After the
kernel is restarted, the library is added to the classpath and can be
used from your python notebook.

.. note::  Some libraries, such as GraphFrames include a python module within it. Pixiedust automatically adds the python file into the SparkContext. However, you must explicitly call **pixiedust.installPackage** at the beginning of every kernel session so that the python modules are added to the SparkContext.

Install from maven search repository
------------------------------------

Go to the maven search site, `search.maven.org <http://search.maven.org/>`_, and look for the package of your choice, like **org.apache.commons**. In the results page, open the link of the component you want, like **commons-proxy**. You get the group ID, artifact ID, and version number to use with the **pixiedust.installPackgage** API.  

By default, pixiedust automatically looks for the following 2 maven repositories: http://repo1.maven.org/maven2 and http://dl.bintray.com/spark-packages/maven. If you use a custom maven repository, you can specify it by using the following base keyword argument:

::

    import pixiedust
    pixiedust.installPackage("groupId:artifactId:0", base="<<url to my custom maven repo>>"


Install a jar file directly from an addressable location
--------------------------------------------------------

To install a jar file that is not packaged in a maven repository, provide the URL to the jar file. Pixiedust will then bypass the maven look up and directly download the jar file from the specified location:

::

   import pixiedust
   pixiedust.installPackage("https://github.com/ibm-cds-labs/spark.samples/raw/master/dist/streaming-twitter-assembly-1.6.jar")


Managing your packages
----------------------

You can uninstall a package by using the following command:

::

   import pixiedust
   pixiedust.uninstallPackage("<<mypackage>>")


You can also list all the packages installed on your system:

::

   import pixiedust
   pixiedust.printAllPackages()

