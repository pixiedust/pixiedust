Custom HTML Attributes
======================

The PixieDust JS runtime listens to click events on any HTML element that has one or more of the custom attributes below, and then transforms the attribute values into a kernel request. The following section describes all the custom attributes available, and how they affect the kernel request executed when a click event is received. 

pd_options
**********
List of key-value pairs that define transient states for the kernel request, according to the following format: ``pd_options="key1=value1;key2=value2;..."``. For example, you can use pd_options to dispatch the current screen to another view. When you use ``pd_entity``, then the pd_options are interpreted as ``display()`` API options (more details below).

.. Note:: You can also use a shorter syntax to define options using the following attribute pattern: ``option_key1="value1"``.

.. Note:: To build the pd_options value for display(), use the display() API in a separate cell. When the correct chart is created, simply copy the options from the cell metadata. (You'll need to use the *View/Cell Toolbar/Edit Metadata* menu to show the "edit metadata" button.) You will also need to transform the JSON to the pd_options attribute format, e.g., no quote in the value, semi-colon separator, and "key=value" format.


pd_entity
*********
Use the pd_entity attribute only if you want to invoke the display() API on specific data. In this case, pd_options must be display-options-specific to the visualization you want to show. The output will be returned by display(), but without the `UI chrome <https://en.wikipedia.org/wiki/Graphical_user_interface#User_interface_and_interaction_design>`_. The value of pd_entity is interpreted as a field to the PixieApp class, e.g., ``pd_entity="filteredDataFrame"``, and requires that the PixieApp instance has a field named filteredDataFrame. If the field is not present, then an error will be raised.

.. Note:: the entity passed by the caller in the run method is stored in a special field called ``pixieapp_entity``. Therefore, using ``pd_entity="pixieapp_entity"`` will direct PixieDust to use the entity passed by the caller. For convenience, the user can also simply use pd_entity (without any value) to do the same thing.

pd_target
*********
By default, the output of a kernel request takes over the entire UI--or output cell or dialog depending on the ``runInDialog`` option). However, you can use ``pd_target="elementId"`` to specify a target element that will receive the output. (Of course the elementId must exist in the current view.) For example:

::
  
      <div id="myTarget{{prefix}}"/>
      <input type="button" pd_options="handlerId=dataframe" pd_entity pd_target="myTarget{{prefix}}" value="click me"/>

In the example above, we define a placeholder div with id ``"myTarget{{prefix}}"`` and use it as a target in the input button.

.. Note:: ``{{prefix}}`` is a Jinja2 notation that means "use the value of the prefix variable, which PixieDust automatically creates to provide a unique id." We need this value to avoid a conflict in case a user calls the PixieApp multiple times within the same notebook.

.. Note:: You can define multiple targets for a particular kernel request. In this case, you'll want to create one or more ``<target>`` elements as children (see the **Custom PixieApp Elements** section for more info).

pd_script
*********
PixieDust lets you run arbitrary Python code using the ``pd_script`` attribute. For example: ``pd_script="self.filteredDataFrame=self.createFilteredDataFrame()"``. pd_script can be used even if pd_entity is used. In this case, the Python script will be executed before the display() call. This behavior can be useful, for example, in creating a sub entity that will be used in the display() call. For example:

::
  
      <div id="myTarget{{prefix}}"/>
      <input type="button" pd_options="handlerId=dataframe" pd_entity="filteredDataFrame" pd_script="self.filteredDataFrame=self.createFilteredDataFrame()" pd_target="myTarget{{prefix}}" value="click me"/>

.. Note:: You can use the ``self`` keyword, which points at the current PixieApp instance.

.. Note:: You can only use one-line Python code (similar to Python lambda). If you need to run more than one line of code, then you'll need to use the pd_script element as a child (see the Custom PixieApp Elements section for more info).

pd_refresh
***********
When you only have the pd_script attribute without pd_target, PixieDust will not refresh the output but will simply execute the pd_script. Using ``pd_refresh`` will force the output to refresh with the current view.

pd_norefresh
************
Similar to pd_refresh, ``pd_norefresh`` forces PixieDust to not refresh the current output target.
