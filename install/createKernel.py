# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2016
# 
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# Inherited from maven-artifact https://github.com/hamnis/maven-artifact
# -------------------------------------------------------------------------------
import os
from traitlets.config.application import Application
from jupyter_client.kernelspec import NoSuchKernel
from ipykernel.kernelspec import KernelSpecManager, write_kernel_spec
from jupyter_client.manager import KernelManager
from jupyter_client.kernelspecapp  import InstallKernelSpec
from six.moves import input
import shutil

class PixiedustInstall(InstallKernelSpec):
    def __init__(self, **kwargs):
        super(PixiedustInstall, self).__init__(**kwargs)
        self.step = 1

    def parse_command_line(self, argv):
        super(InstallKernelSpec, self).parse_command_line(argv)

        self.pixiedust_home = os.environ.get("PIXIEDUST_HOME", os.path.expanduser('~'))
        answer = self.confirm(
            "Step 1: PIXIEDUST_HOME: {0}".format(self.pixiedust_home)
        )

        if ( answer != 'y'):
            self.pixiedust_home = input(self.hilite("Please enter a PIXIEDUST_HOME location: "))
            if not os.path.exists(self.pixiedust_home):
                create = self.confirm("Directory {0} does not exist".format(self.pixiedust_home), "Create")
                if create != 'y':
                    self.exit(1)
                else:
                    os.makedirs(self.pixiedust_home)

        self.spark_home = os.environ.get("SPARK_HOME", None) 
        if self.spark_home:
            answer = self.confirm(
                "Step 2: SPARK_HOME: {0}".format(self.spark_home)
            )
            if answer != 'y':
                self.spark_home = None

        if self.spark_home is None:
            self.spark_home = input(self.hilite("Step 2: Please enter a SPARK_HOME location: "))
        
        if not os.path.exists(self.spark_home):
            print("{0} does not exist".format(self.spark_home))
            self.exit(1)

        self.scala_home = os.environ.get("SCALA_HOME", None)
        if self.scala_home:
            answer = self.confirm(
                "Step 3: SCALA_HOME: {0}".format(self.scala_home)
            )
            if answer != 'y':
                self.scala_home = None

        if self.scala_home is None:
            self.scala_home = input(self.hilite("Step 3: Please enter a SCALA_HOME location: "))

        if not os.path.exists(self.scala_home):
            print("{0} does not exist".format(self.scala_home))
            self.exit(1)

        self.kernelName = "Python with Pixiedust"
        answer = self.confirm(
            "Step 4: Kernel Name: {0}".format(self.kernelName)
        )
        if answer != 'y':
            self.kernelName = input(self.hilite("Step 4: Please enter a Kernel Name: "))

        try:
            km = KernelManager(kernel_name=self.kernelName)
            km.kernel_spec
            answer = self.confirm(
                "Kernel '{0}' already exists".format(self.kernelName), "Override"
            )
            if answer != 'y':
                self.exit(1)
        except NoSuchKernel:
            pass

        dest = self.createKernelSpec()
        print("Kernel {0} successfully created in {1}".format(self.kernelName, dest))

    def createKernelSpec(self):
        try:
            libFiles = os.listdir("{0}/python/lib".format(self.spark_home))
            py4j_zip = list(filter( lambda filename: "py4j" in filename, libFiles))[0]
        except:
            print('Unable to find py4j in SPARK_HOME: {0}'.format(self.spark_home))
            self.exit(1)

        overrides={
            "display_name": self.kernelName,
            "argv": [
                "python",
                "-m",
                "ipykernel",
                "-f",
                "{connection_file}"
            ],
            "env": {
                "PIXIEDUST_HOME": self.pixiedust_home,
                "SCALA_HOME": "{0}".format(self.scala_home),
                "SPARK_HOME": "{0}".format(self.spark_home),
                "PYTHONPATH": "{0}/python/:{0}/python/lib/{1}".format(self.spark_home, py4j_zip),
                "PYTHONSTARTUP": "{0}/python/pyspark/shell.py".format(self.spark_home),
                "PYSPARK_SUBMIT_ARGS": "--driver-class-path {0}/data/libs/* --master local[10] pyspark-shell".format(self.pixiedust_home),
                "SPARK_DRIVER_MEMORY":"10G",
                "SPARK_LOCAL_IP":"127.0.0.1"
            }
        }
        path = write_kernel_spec(overrides=overrides)
        dest = KernelSpecManager().install_kernel_spec(path, kernel_name=self.kernelName, user=True)
        # cleanup afterward
        shutil.rmtree(path)
        return dest

    def confirm(self, message, action="Keep"):
        answer = input(self.hilite(message) + "\n\t" + action + " y/n [y]? ")
        return 'y' if answer == '' else answer

    def hilite(self, message):
        return '\x1b[%sm%s\x1b[0m' % (';'.join(['32', '1']), message)

    def start(self):
        pass