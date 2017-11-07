PixieGateway
============

**What is PixieGateway?**

PixieGateway is a web application server that is responsible for loading and running PixieApps. It allows PixieDust users to free their apps and charts from the confines of data science notebooks, in order to share their work as web apps or standalone webpages. The goal is for developers and data scientists to more easily make the analytics in their notebooks available to line-of-business colleagues.

PixieGateway is built on top of the `Jupyter Kernel Gateway <https://github.com/jupyter/kernel_gateway>`_ and therefore follows a similar architecture:

.. image:: _images/pixiegateway_architecture.png
   :width: 800 px

.. toctree::
   :maxdepth: 2


   install-pixiegateway
   chart-sharing
   pixieapp-publishing
   admin-pixiegateway