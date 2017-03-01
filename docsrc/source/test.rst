Test
===========

PixieDust provides several `notebooks <https://github.com/ibm-cds-labs/pixiedust/tree/master/tests>`_ that you can run to test and check stability of various features. Tests are maintained using `Travis CI <https://travis-ci.org/ibm-cds-labs/pixiedust>`_.

The test script, `runPixiedustNotebooks.py <https://github.com/ibm-cds-labs/pixiedust/blob/master/tests/runPixiedustNotebooks.py>`_, runs whenever an update is pushed to the repository or a pull request is made. The test script runs through each of the notebooks in the `tests <https://github.com/ibm-cds-labs/pixiedust/tree/master/tests>`_ directory. 

Locally Running the Tests
-------------------------

Using VSCode
************

1. Install the `python extension <http://donjayamanne.github.io/pythonVSCode/>`_ into VSCode
2. Open the pixiedust repository/directory in VSCode 
3. Set the **python.pythonPath** in the *User Settings* of the VSCode Preferences to the appropriate location of your python directory
4. From the Debug View, click on the Configure gear and select Python
5. Edit the ``launch.json`` and add a new object (or edit an existing one) in *configurations*

::

	{
	  "name": "pixiedust test",
	  "type": "python",
	  "request": "launch",
	  "stopOnEntry": false,
	  "pythonPath": "${config.python.pythonPath}",
	  "program": "${workspaceRoot}/tests/runPixiedustNotebooks.py",
	  "console": "integratedTerminal",
	  "debugOptions": [
	    "WaitOnAbnormalExit",
	    "WaitOnNormalExit"
	  ],
	  "env": {
	    "SPARK_HOME": "/Users/path/to/spark",
	    "SCALA_HOME": "/Users/path/to/scala",
	    "PIXIEDUST_TEST_INPUT": "${workspaceRoot}/tests"
	  }
	}

Update the ``SPARK_HOME`` and ``SCALA_HOME`` entries accordingly. If you want, update ``PIXIEDUST_TEST_INPUT`` to where test notebooks to run are located
	
6. Select the newly created or updated **pixiedust test** configuration from dropdown in the Debug view
7. Click on the Debug green arrow, to run the configuration

The Integrated Terminal should show the test output as the tests are running.

Using Command Line
******************

From a terminal window:

1. Go into the ``tests`` directory in the pixiedust repository/directory
2. Set the following environment variables accordingly  

::

	SPARK_HOME=/Users/path/to/spark
	SCALA_HOME=/Users/path/to/scala
	PIXIEDUST_TEST_INPUT=/Users/path/to/test/notebooks

3.  Run the command ``python runPixiedustNotebooks.py``

The terminal window should show the test output as the tests are running.
