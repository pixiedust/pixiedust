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
import re
import requests
import shutil
import string
import subprocess
import sys
import tarfile
import tempfile
from ipykernel.kernelspec import KernelSpecManager, write_kernel_spec
from jupyter_client.kernelspec import NoSuchKernel
from jupyter_client.manager import KernelManager
from jupyter_client.kernelspecapp  import InstallKernelSpec
from six.moves import input
from traitlets.config.application import Application


class PixiedustInstall(InstallKernelSpec):
    def __init__(self, **kwargs):
        super(PixiedustInstall, self).__init__(**kwargs)
        self.pixiedust_home = None
        self.spark_home = None
        self.spark_download_versions = ['1.6.3', '2.0.2', '2.1.0']
        self.spark_download_urls = {
            '1.6.3': 'http://d3kbcqa49mib13.cloudfront.net/spark-1.6.3-bin-hadoop2.6.tgz',
            '2.0.2': 'http://d3kbcqa49mib13.cloudfront.net/spark-2.0.2-bin-hadoop2.7.tgz',
            '2.1.0': 'http://d3kbcqa49mib13.cloudfront.net/spark-2.1.0-bin-hadoop2.7.tgz'
        }
        self.scala_home = None
        self.scala_download_urls = {
            '2.10': 'http://downloads.lightbend.com/scala/2.10.6/scala-2.10.6.tgz',
            '2.11': 'http://downloads.lightbend.com/scala/2.11.8/scala-2.11.8.tgz'
        }

    def parse_command_line(self, argv):
        silent = "--silent" in argv
        silent_spark_version = None
        if silent:
            argv.remove("--silent")
            arg_str = None
            for i, arg in enumerate(argv):
                if arg.startswith("--spark"):
                    arg_str = arg
                    silent_spark_version = arg_str[len("--spark")+1:]
                    if silent_spark_version not in self.spark_download_versions:
                        print("Invalid Spark version {}".format(silent_spark_version))
                        self.exit(1)
                    break
            if arg_str:
                argv.remove(arg_str)
        super(InstallKernelSpec, self).parse_command_line(argv)

        self.pixiedust_home = os.environ.get("PIXIEDUST_HOME", "{}{}pixiedust".format(os.path.expanduser('~'), os.sep))
        if silent:
            answer = 'y'
        else:
            answer = self.confirm(
                "Step 1: PIXIEDUST_HOME: {0}".format(self.pixiedust_home)
            )

        if answer != 'y':
            self.pixiedust_home = input(self.hilite("Please enter a PIXIEDUST_HOME location: "))
            if not os.path.exists(self.pixiedust_home):
                create = self.confirm("Directory {0} does not exist".format(self.pixiedust_home), "Create")
                if create != 'y':
                    self.exit(1)
                else:
                    os.makedirs(self.pixiedust_home)

        download_spark = False
        if silent:
            self.spark_home = os.environ.get("SPARK_HOME", None)
            if not self.spark_home:
                download_spark = True
                self.spark_home = "{}{}spark".format(os.path.expanduser('~'), os.sep)
        else:
            first_prompt = True
            while True:
                self.spark_home = os.environ.get("SPARK_HOME", None)
                if self.spark_home:
                    answer = self.confirm(
                        "Step 2: SPARK_HOME: {0}".format(self.spark_home)
                    )
                    if answer != 'y':
                        self.spark_home = input(self.hilite("Step 2: Please enter a SPARK_HOME location: "))
                else:
                    if first_prompt:
                        first_prompt = False
                        prompt = "Step 2: Please enter a SPARK_HOME location: "
                    else:
                        prompt = "Please enter a SPARK_HOME location: "
                    self.spark_home = input(self.hilite(prompt))
                while self.spark_home.rfind(os.sep) == len(self.spark_home) - 1:
                    self.spark_home = self.spark_home[0:len(self.spark_home)-1]
                if not os.path.exists(self.spark_home):
                    create = self.confirm("Directory {0} does not exist".format(self.spark_home), "Create")
                    if create != 'y':
                        continue
                    else:
                        os.makedirs(self.spark_home)
                        download_spark = True
                        break
                elif not os.path.exists('{}{}bin{}pyspark'.format(self.spark_home, os.sep, os.sep)):
                    download = self.confirm("Directory {0} does not contain a valid SPARK install".format(self.spark_home), "Download Spark")
                    if download == 'y':
                        download_spark = True
                        break
                else:
                    break

        if download_spark:
            self.download_spark(silent, silent_spark_version)

        scala_version = None
        spark_version = self.get_spark_version()
        if spark_version is None:
            print("Unable to obtain Spark version")
            self.exit(1)
        elif spark_version[0] == 1:
            scala_version = '2.10'  # Spark 1.x = Scala 2.10
        elif spark_version[0] == 2:
            scala_version = '2.11'  # Spark 2.x = Scala 2.11
        else:
            print("Invalid Spark version {}".format(spark_version))
            self.exit(1)

        download_scala = False
        if silent:
            self.scala_home = os.environ.get("SCALA_HOME", None)
            if not self.scala_home:
                download_scala = True
                self.scala_home = "{}{}scala".format(os.path.expanduser('~'), os.sep)
        else:
            first_prompt = True
            while True:
                self.scala_home = os.environ.get("SCALA_HOME", None)
                if self.scala_home:
                    answer = self.confirm(
                        "Step 3: SCALA_HOME: {0}".format(self.scala_home)
                    )
                    if answer != 'y':
                        self.scala_home = input(self.hilite("Step 3: Please enter a SCALA_HOME location: "))
                else:
                    if first_prompt:
                        first_prompt = False
                        prompt = "Step 3: Please enter a SCALA_HOME location: "
                    else:
                        prompt = "Please enter a SCALA_HOME location: "
                    self.scala_home = input(self.hilite(prompt))
                while self.scala_home.rfind(os.sep) == len(self.scala_home) - 1:
                    self.scala_home = self.scala_home[0:len(self.scala_home)-1]
                if not os.path.exists(self.scala_home):
                    create = self.confirm("Directory {0} does not exist".format(self.scala_home), "Create")
                    if create != 'y':
                        continue
                    else:
                        os.makedirs(self.scala_home)
                        download_scala = True
                        break
                elif not os.path.exists('{}{}bin{}scala'.format(self.scala_home, os.sep, os.sep)):
                    download = self.confirm(
                        "Directory {0} does not contain a valid SCALA install".format(self.scala_home),
                        "Download Scala"
                    )
                    if download == 'y':
                        download_scala = True
                        break
                else:
                    installed_scala_version = self.get_scala_version()
                    if not installed_scala_version or (str(installed_scala_version[0]) + '.' + str(installed_scala_version[1])) != scala_version:
                        print("A different version of Scala {0} is already installed in this directory.".format(installed_scala_version))
                        continue
                    else:
                        break

        if download_scala:
            self.download_scala(scala_version)

        self.kernelName = "Python with Pixiedust (Spark {}.{})".format(spark_version[0], spark_version[1])
        if silent:
            answer = 'y'
        else:
            answer = self.confirm(
                "Step 4: Kernel Name: {0}".format(self.kernelName)
            )
        if answer != 'y':
            self.kernelName = input(self.hilite("Please enter a Kernel Name: "))

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

    def get_spark_version(self):
        pyspark = "{}{}bin{}pyspark".format(self.spark_home, os.sep, os.sep)
        pyspark_out = subprocess.check_output([pyspark, "--version"], stderr=subprocess.STDOUT).decode("utf-8")
        match = re.search(".*version[^0-9]*([0-9]*[^.])\.([0-9]*[^.])\.([0-9]*[^.]).*", str(pyspark_out))
        if match and len(match.groups()) > 2:
            return int(match.group(1)), int(match.group(2))
        else:
            return None

    def download_spark(self, silent, silent_spark_version):
        while True:
            spark_default_version = self.spark_download_versions[len(self.spark_download_versions)-1]
            spark_download_versions_str = ', '.join(self.spark_download_versions) + ' [{}]'.format(spark_default_version)
            if silent:
                if silent_spark_version:
                    spark_version = silent_spark_version
                else:
                    spark_version = spark_default_version
            else:
                spark_version = input(
                    self.hilite("What version would you like to download? {}: ".format(spark_download_versions_str))
                )
            if len(spark_version.strip()) == 0:
                spark_version = self.spark_download_versions[len(self.spark_download_versions)-1]
            elif spark_version not in self.spark_download_versions:
                print("{0} is not a valid version".format(self.spark_home))
                continue
            spark_download_url = self.spark_download_urls[spark_version]
            spark_download_file = spark_download_url[spark_download_url.rfind('/')+1:spark_download_url.rfind('.')]
            print("SPARK_HOME will be set to {}{}{}".format(self.spark_home, os.sep, spark_download_file))
            print("Downloading Spark {}".format(spark_version))
            temp_file = self.download_file(spark_download_url)
            print("Extracting Spark {} to {}".format(spark_version, self.spark_home))
            self.extract_temp_file(temp_file, self.spark_home)
            self.delete_temp_file(temp_file)
            self.spark_home = "{}{}{}".format(self.spark_home, os.sep, spark_download_file)
            os.environ["SPARK_HOME"] = self.spark_home
            break

    def get_scala_version(self):
        scala = "{}{}bin{}scala".format(self.scala_home, os.sep, os.sep)
        try:
            scala_out = subprocess.check_output([scala, "-version"], stderr=subprocess.STDOUT).decode("utf-8")
        except subprocess.CalledProcessError as cpe:
            scala_out = cpe.output
        match = re.search(".*version[^0-9]*([0-9]*[^.])\.([0-9]*[^.])\.([0-9]*[^.]).*", str(scala_out))
        if match and len(match.groups()) > 2:
            return int(match.group(1)), int(match.group(2))
        else:
            return None

    def download_scala(self, scala_version):
        while True:
            scala_download_url = self.scala_download_urls[scala_version]
            scala_download_file = scala_download_url[scala_download_url.rfind('/')+1:scala_download_url.rfind('.')]
            print("SCALA_HOME will be set to {}/{}".format(self.scala_home, scala_download_file))
            print("Downloading Scala {}".format(scala_version))
            temp_file = self.download_file(scala_download_url)
            print("Extracting Scala {} to {}".format(scala_version, self.scala_home))
            self.extract_temp_file(temp_file, self.scala_home)
            self.delete_temp_file(temp_file)
            self.scala_home = "{}{}{}".format(self.scala_home, os.sep, scala_download_file)
            os.environ["SCALA_HOME"] = self.scala_home
            break

    @staticmethod
    def download_file(url, suffix=None):
        if suffix is None:
            suffix = url[url.rfind('.'):]
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix)
        response = requests.get(url, stream=True)
        total_bytes = int(response.headers["content-length"])
        bytes_read = 0
        for chunk in response.iter_content(chunk_size=1048576):
            temp_file.write(chunk)
            temp_file.flush()
            bytes_read += len(chunk)
            print(" {} %".format(int(((bytes_read*1.0)/total_bytes)*100)))
            sys.stdout.write("\033[F")
            sys.stdout.flush()
        print("      ")
        sys.stdout.write("\033[F")
        sys.stdout.flush()
        return temp_file

    @staticmethod
    def delete_temp_file(temp_file):
        temp_file.close()

    @staticmethod
    def extract_temp_file(temp_file, path):
        tar = tarfile.open(temp_file.name, "r:gz")
        for i, member in enumerate(tar.getmembers()):
            tar.extract(member, path)
            print(" {} %".format(int(((i*1.0)/len(tar.getmembers()))*100)))
            sys.stdout.write("\033[F")
            sys.stdout.flush()
        print("      ")
        sys.stdout.write("\033[F")
        sys.stdout.flush()
        tar.close()

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
        dest = KernelSpecManager().install_kernel_spec(path, kernel_name=''.join(ch for ch in self.kernelName if ch.isalnum()), user=True)
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