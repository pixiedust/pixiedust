Custom Elements
===============

<target>
********
Child element to the clickable source element. ``<target>`` can have any of the `custom PixieApp HTML attributes <html-attributes-pixieapps.html>`_ defined above. For example:  

::
  
      <button type="button">Multiple Targets
            <target pd_target="target{{prefix}}" 
                pd_entity
                pd_options="handlerId=dataFrame"/>
            <target pd_target="target2{{prefix}}"
                pd_entity  
                pd_options="keyFields=zone;aggregation=AVG;handlerId=barChart;valueFields=unique_customers;rowCount=100/">
      </button>

<pd_script>
***********
Contains Python code as child text. It has the same meaning as the pd_script attribute, except that it can contain multiple lines of Python code. Because indentation is important in Python, be careful to not have empty space in your code---regardless of the indentation level of your HTML markup. For example:

::
  
    <pd_script>
  import json
  print(json.dumps(self.myJson)
    </pd_script>
