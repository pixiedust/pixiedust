PixieGateway
============

**What is PixieGateway?**

PixieGateway is a web application server used for sharing charts and running PixieApps as web applications. It allows PixieDust users to free their apps and charts from the confines of data science notebooks, in order to better share their work. The goal is for developers and data scientists to more easily make the analytics in their notebooks available to line-of-business colleagues and other people less comfortable with Jupyter Notebooks.

PixieGateway is built on top of the `Jupyter Kernel Gateway <https://github.com/jupyter/kernel_gateway>`_ and therefore follows a similar architecture:

.. image:: _images/pixiegateway_architecture.png
   :width: 800 px

While designed to be used with the PixieDust package, PixieGateway is developed in a separate GitHub repository at https://github.com/ibm-watson-data-lab/pixiegateway . You’ll find more details in the sub-topics here.

.. toctree::
   :maxdepth: 2


   install-pixiegateway
   chart-sharing
   pixieapp-publishing
