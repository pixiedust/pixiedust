Install PixieGateway
====================

Local Install
-------------

If you want to demo PixieApp publishing locally, follow these instructions. If you’d rather deploy your application to the cloud, see the section below on using Kubernetes on Bluemix.

To start, install the pixiegateway package from PyPi. On the command line, run the following: (Note: PixieGateway supports both Python 2.7 and 3.x)

::

  pip install pixiegateway

Then you can start the PixieGateway with a simple command:

::

  jupyter pixiegateway --port <portnumber>

Example output:

::

  dtaieb$ jupyter pixiegateway --port 8899
  [PixieGatewayApp] Kernel started: b5be0b3b-a018–4ace-95d1-d94b556a0bfe
  kernel client initialized
  [PixieGatewayApp] Jupyter Kernel Gateway at http://127.0.0.1:8899

Now, go to ``http://localhost:<portnumber>/pixieapps`` to review and use your apps.

[optional] Running PixieGateway in Kubernetes on IBM Bluemix
------------------------------------------------------------

If you’re new to Kubernetes on the IBM Bluemix container service, `read this intro article <https://medium.com/ibm-watson-data-lab/zero-to-kubernetes-on-the-ibm-bluemix-container-service-fd104fd193c1>`_ that explains the basics of using the service with the ``bx`` and ``kubectl`` command-line tools.

Here are the steps to install PixieGateway using Kubernetes on Bluemix:

1. Download the `Kubernetes CLI <https://kubernetes.io/docs/tasks/tools/install-kubectl/>`_ and the `Bluemix CLI <https://console.bluemix.net/docs/cli/reference/bluemix_cli/get_started.html#getting-started>`_.

2. ``bx login [-sso] -a https://api.ng.bluemix.net``

3. ``bx target -o <YOUR_ORG> -s <YOUR_SPACE>``

4. ``bx plugin install container-service -r Bluemix``

5. ``bx cs init``

6. If not already done, create a cluster: ``bx cs cluster-create --name my-cluster``

7. Verify that the cluster is correctly created (this may take a few minutes): ``bx cs clusters``

8. Download the cluster config: ``bx cs cluster-config my-cluster``

9. Run the export command returned by the command above, e.g., ``export KUBECONFIG=/Users/dtaieb/.bluemix/plugins/container-service/clusters/davidcluster/kube-config-hou02-davidcluster.yml``

10. Create the deployment: ``kubectl create -f https://github.com/ibm-watson-data-lab/pixiegateway/raw/master/etc/deployment.yml``

11. Create the service: ``kubectl create -f https://github.com/ibm-watson-data-lab/pixiegateway/raw/master/etc/service.yml``

12. Verify the pods: ``kubectl get pods``

13. Verify the nodes: ``kubectl get nodes``

14. Verify the services: ``kubectl get services``

15. Finally, you can get the public ip address of the server: ``bx cs workers my-cluster``

.. image:: _images/bx-cs-workers.png
   :width: 800 px

16. To check that the install worked, enter the following URL in your browser: ``http://<publicIP>:32222/pixieapps``. You’ll be able to interact with your PixieApp-published web apps from there.

.. image:: _images/pixiegateway-list.png
   :width: 800 px

17. **Optional:** In the future, if you need to update the PixieGateway version, you do not have to retrace the previous steps. Instead, simply delete the Kubernetes pod, which will cause Docker to restart and automatically pull down a new version of PixieDust, like so: ``kubectl delete pod <name>``. Here, ``<name>`` is the pod’s name obtained with the command: ``kubectl get pods``.

.. Note:: The deployed PixieApps are not stored in a persisted volume, so deleting the pod will also delete them, and you’ll have to re-publish.