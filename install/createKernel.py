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
# -------------------------------------------------------------------------------
import json
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
from lxml import etree
import nbformat

class PixiedustInstall(InstallKernelSpec):
    def __init__(self, **kwargs):
        super(PixiedustInstall, self).__init__(**kwargs)
        self.pixiedust_home = None
        self.spark_home = None
        self.spark_download_versions = ['1.6.3', '2.0.2', '2.1.0', '2.2.0']
        self.spark_download_urls = {
            '1.6.3': 'http://d3kbcqa49mib13.cloudfront.net/spark-1.6.3-bin-hadoop2.6.tgz',
            '2.0.2': 'http://d3kbcqa49mib13.cloudfront.net/spark-2.0.2-bin-hadoop2.7.tgz',
            '2.1.0': 'http://d3kbcqa49mib13.cloudfront.net/spark-2.1.0-bin-hadoop2.7.tgz',
            '2.2.0': 'https://d3kbcqa49mib13.cloudfront.net/spark-2.2.0-bin-hadoop2.7.tgz'
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

        self.pixiedust_bin = os.path.join(self.pixiedust_home, "bin")
        download_spark = False
        if silent:
            self.spark_home = os.environ.get("SPARK_HOME", None)
            if not self.spark_home:
                download_spark = True
                self.spark_home = "{}{}spark".format(os.path.expanduser('~'), os.sep)
        else:
            first_prompt = True
            while True:
                self.spark_home = os.environ.get("SPARK_HOME", self.ensureDir(os.path.join(self.pixiedust_bin, "spark" )))
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
                    existingInstalls = [d for d in os.listdir(self.spark_home) if os.path.exists(os.path.join(self.spark_home,d,'bin','pyspark'))]
                    if len(existingInstalls) == 0:
                        download = self.confirm("Directory {0} does not contain a valid SPARK install".format(self.spark_home), "Download Spark")
                        if download == 'y':
                            download_spark = True
                            break
                    else:
                        existingInstalls.append("Create a new spark Install")
                        print("Select an existing spark install or create a new one")
                        message = "\n".join(["{}. {}".format(k+1,v) for k,v in enumerate(existingInstalls)])
                        while True:
                            try:
                                answer = int(input(self.hilite(message) + "\n\tEnter your selection: ")) - 1
                                if answer < 0 or answer >= len(existingInstalls):
                                    raise Exception("Please pick a number within the specified values")
                                break;
                            except Exception as e:
                                print("Invalid selection: {}".format(e))

                        download_spark = (answer == len(existingInstalls) - 1)
                        if not download_spark:
                            self.spark_home = os.path.join(self.spark_home, existingInstalls[answer])
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

        #download spark-cloudant
        sparkCloudantUrl = "https://github.com/cloudant-labs/spark-cloudant/releases/download/v1.6.4/cloudant-spark-v1.6.4-167.jar"
        if spark_version[0] == 2:
            sparkCloudantUrl = "https://github.com/cloudant-labs/spark-cloudant/releases/download/v2.0.0/cloudant-spark-v2.0.0-185.jar"

        try:
            self.sparkCloudantPath = self.downloadFileToDir( sparkCloudantUrl, targetDir = self.pixiedust_bin )
            print("downloaded spark cloudant jar: {0}".format(self.sparkCloudantPath))
        except Exception as e:
            print("Error downloading Cloudant Jar: {}. Install will continue without the spark Cloudant connector".format(e))

        #download spark csv connector if in spark 1.6
        self.sparkCSVPath = None
        self.commonsCSVPath = None
        if spark_version[0] == 1:
            try:
                self.sparkCSVPath = self.downloadPackage("com.databricks:spark-csv_2.10:1.5.0")
                self.commonsCSVPath = self.downloadPackage("org.apache.commons:commons-csv:0")
            except Exception as e:
                print("Error downloading csv connector Jar: {}. Install will continue without it".format(e))

        download_scala = False
        if silent:
            self.scala_home = os.environ.get("SCALA_HOME", None)
            if not self.scala_home:
                download_scala = True
                self.scala_home = "{}{}scala".format(os.path.expanduser('~'), os.sep)
        else:
            first_prompt = True
            while True:
                self.scala_home = os.environ.get("SCALA_HOME", self.ensureDir(os.path.join(self.pixiedust_bin, "scala" )))
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
                    def acceptScalaVersion(dir):
                        version = self.get_scala_version_from_dir(os.path.join(self.scala_home,dir))
                        return version is not None and str(version[0]) + '.' + str(version[1]) == scala_version
                    existingInstalls = [d for d in os.listdir(self.scala_home) if acceptScalaVersion(d)]
                    if len(existingInstalls) == 0:
                        download = self.confirm("Directory {0} does not contain a valid scala install".format(self.scala_home), "Download Scala")
                        if download == 'y':
                            download_scala = True
                            break
                    else:
                        existingInstalls.append("Create a new scala Install")
                        print("Select an existing scala install or create a new one")
                        message = "\n".join(["{}. {}".format(k+1,v) for k,v in enumerate(existingInstalls)])
                        while True:
                            try:
                                answer = int(input(self.hilite(message) + "\n\tEnter your selection: ")) - 1
                                if answer < 0 or answer >= len(existingInstalls):
                                    raise Exception("Please pick a number within the specified values")
                                break;
                            except Exception as e:
                                print("Invalid selection: {}".format(e))

                        download_scala = (answer == len(existingInstalls) - 1)
                        if not download_scala:
                            self.scala_home = os.path.join(self.scala_home, existingInstalls[answer])
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

        self.pixiedust_notebooks_dir = os.path.join( self.pixiedust_home, "notebooks")
        if not os.path.isdir(self.pixiedust_notebooks_dir):
            os.makedirs(self.pixiedust_notebooks_dir)
        print("Downloading intro notebooks into {}".format(self.pixiedust_notebooks_dir))
        self.downloadIntroNotebooks()

        print("\n\n{}".format("#"*100))
        print("#\tCongratulations: Kernel {0} was successfully created in {1}".format(self.kernelName, dest))
        print("#\tYou can start the Notebook server with the following command:")
        print("#\t\t{}".format(
            self.hilite("jupyter notebook {}".format(self.pixiedust_notebooks_dir))
        ))
        print("{}".format("#"*100))

    def ensureDir(self, parentLoc):
        if not os.path.isdir(parentLoc):
            os.makedirs(parentLoc)
        return parentLoc

    def downloadFileToDir( self, url, targetDir ):
        index = url.rfind('/')
        fileName = url[index+1:] if index >= 0 else url
        localPath = os.path.join(targetDir, fileName)
        if not os.path.isfile(localPath ):
            try:
                with open(localPath, "wb") as targetFile:
                    self.download_file(url, targetFile = targetFile)
            except:
                os.remove(localPath)
                raise
        return localPath

    def downloadPackage(self, packageId):
        if packageId.startswith("http://") or packageId.startswith("https://") or packageId.startswith("file://"):
            #direct download
            return self.downloadFileToDir( packageId, targetDir=self.pixiedust_bin)
        else:
            #assume maven id, resolve it
            parts = packageId.split(":")
            bases = ["http://repo1.maven.org/maven2", "http://dl.bintray.com/spark-packages/maven"]
            response = None
            for base in bases:
                url = None
                if parts[2] == '0':
                    #resolve version
                    metadataUrl = "{0}/{1}/maven-metadata.xml".format(base, "/".join([parts[0].replace(".", "/"), parts[1]]))
                    r = requests.get(metadataUrl, stream=True)
                    if r.ok:
                        parts[2] = etree.parse(r.raw).xpath("/metadata/versioning/versions/version[last()]/text()")[0]
                if parts[2] != '0':
                    url = "{0}/{1}/{2}-{3}.jar".format(
                        base, 
                        "/".join([parts[0].replace(".", "/"), parts[1], parts[2]]),
                        parts[1],
                        parts[2]
                    )
                    response = requests.get(url, stream=True)
                    if response.ok:
                        break

            if response is None or not response.ok:
                raise Exception("Unable to resolve package {}".format(packageId))

            return self.downloadFileToDir( url, targetDir=self.pixiedust_bin)

    def downloadIntroNotebooks(self):
        #download the Intro.txt file that contains all the notebooks to download
        response = requests.get("https://github.com/ibm-watson-data-lab/pixiedust/raw/master/notebook/Intro.txt")
        if not response.ok:
            raise Exception("Unable to read the list of Intro Notebooks")

        notebookNames = response.content.decode().split("\n")
        introNotebooksUrls = [
            "https://github.com/ibm-watson-data-lab/pixiedust/raw/master/notebook/" + n for n in notebookNames if n != ""
        ]
        for url in introNotebooksUrls:
            print("...{0}".format(url))
            try:
                path = self.downloadFileToDir(url, targetDir=self.pixiedust_notebooks_dir)
                #update kernel name and display_name
                f = open(path, 'r')
                contents = f.read()
                f.close()
                nb=nbformat.reads(contents, as_version=4)
                nb.metadata.kernelspec.name=self.kernelInternalName
                nb.metadata.kernelspec.display_name = self.kernelName
                f = open(path, 'w')
                f.write(json.dumps(nb))
                f.close()
                print("\033[F\033[F")
                print("...{0} : {1}".format(url, self.hilite("done")))
            except Exception as e:
                print("\033[F\033[F")
                print("...{0} : {1}".format(url, self.hilite("Error {}".format(e))))
                

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

    def get_scala_version_from_dir(self, dir):
        scala = os.path.join(dir, "bin", "scala")
        try:
            scala_out = subprocess.check_output([scala, "-version"], stderr=subprocess.STDOUT).decode("utf-8")
        except subprocess.CalledProcessError as cpe:
            scala_out = cpe.output
        match = re.search(".*version[^0-9]*([0-9]*[^.])\.([0-9]*[^.])\.([0-9]*[^.]).*", str(scala_out))
        if match and len(match.groups()) > 2:
            return int(match.group(1)), int(match.group(2))
        else:
            return None

    def get_scala_version(self):
        return self.get_scala_version_from_dir(self.scala_home)

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
    def download_file(url, suffix=None, targetFile = None):
        if suffix is None:
            suffix = url[url.rfind('.'):]

        if targetFile is None:
            targetFile = tempfile.NamedTemporaryFile(suffix=suffix)

        response = requests.get(url, stream=True)
        if not response.ok:
            raise Exception("{}".format(response.status_code))

        total_bytes = int(response.headers.get("content-length", 0))
        bytes_read = 0
        for chunk in response.iter_content(chunk_size=1048576):
            targetFile.write(chunk)
            targetFile.flush()
            bytes_read += len(chunk)
            if total_bytes <= bytes_read:
                total_bytes = bytes_read
            print(" {} %".format(int(((bytes_read*1.0)/total_bytes)*100)))
            sys.stdout.write("\033[F")
            sys.stdout.flush()
        print("      ")
        sys.stdout.write("\033[F")
        sys.stdout.flush()
        return targetFile

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
                "PYSPARK_SUBMIT_ARGS": "--jars {0} --driver-class-path {1} --master local[10] pyspark-shell".format(
                    self.sparkCloudantPath,
                    ":".join([x for x in [self.pixiedust_home + "/data/libs/*" ,self.sparkCSVPath,self.commonsCSVPath] if x is not None]),
                ),
                "SPARK_DRIVER_MEMORY":"10G",
                "SPARK_LOCAL_IP":"127.0.0.1"
            }
        }
        path = write_kernel_spec(overrides=overrides)
        self.kernelInternalName = ''.join(ch for ch in self.kernelName if ch.isalnum()).lower()
        print("self.kernelInternalName {}".format(self.kernelInternalName))
        dest = KernelSpecManager().install_kernel_spec(path, kernel_name=self.kernelInternalName, user=True)
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