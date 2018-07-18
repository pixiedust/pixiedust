Dynamic Values
==============

In some cases, you might want to include values that depend on client-side user input (e.g., write a pd_script that executes a query provided as input by the user). To do that, you can use the ``"$val(<id>)"`` directive, which acts as a macro that will be resolved at the time the kernel request is executed. 

"$val(<id>)" takes one argument that can be one of the following: 

- **html element id:** The macro is replaced by the value of the HTML element specified by the id. For example:

::
  
  <pd_script>
  self.executeQuery("$val(inputId)") 
  </pd_script>

- **JavaScript function:** The macro is replaced by the value returned by the specified JavaScript function. For example:

::
  
  <script>
  function resValue(){
    return "my_query";
  }
  </script>

  ...

  <pd_script>
  self.executeQuery("$val(resValue)")
  </pd_script>

.. Note:: dynamic values are currently supported in `pd_options <html-attributes-pixieapp.html#pd-options>`_ and `pd_script <html-attributes-pixieapp.html#pd-script>`_.