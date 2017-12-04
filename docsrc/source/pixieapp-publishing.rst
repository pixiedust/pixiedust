PixieApp Publishing
===================

**The Publication Process**

Once you have developed your PixieApp in a Jupyter Notebook, here's how you can publish it to the web

Click on the **publish icon** (the electric plug icon 🔌 in the upper-right corner) to deploy the PixieApp into the PixieGateway.

.. image:: _images\pixieapp-publish-button.png

The Publish Configuration dialog contains the following panels:

1. Basic configuration info, such as server address, page title, and page icon. The only required field is the PixieGateway server location. You can simply enter it, and click the **Publish** button.

.. image:: _images\publish-pixieapp-config.png
   :width: 800 px

2. You can also view more details. The Imports pane contains a list of package dependencies (automatically detected by static code analysis).

.. image:: _images\publish-pixieapp-imports.png
   :width: 800 px

3. And finally, you can view the Kernel Spec information.

.. image:: _images\publish-pixieapp-kernel.png
   :width: 800 px

If all goes well, you should see a dialog similar to the following:

.. image:: _images\pixieapp-publish-success.png
   :width: 800 px

Click on the provided link and start using the PixieApp as a regular web application.

.. image:: _images\pixieapp-published-final.png
   :width: 800 px
