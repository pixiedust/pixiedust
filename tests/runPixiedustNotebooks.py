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
import os
import sys
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert.preprocessors.execute import CellExecutionError
import logging
from ipykernel.kernelspec import KernelSpecManager, write_kernel_spec
from jupyter_client.manager import KernelManager
from jupyter_client.kernelspec import NoSuchKernel
import shutil

__TEST_KERNEL_NAME__ = "PixiedustTravisTest"

if "debug" in os.environ:
    logging.basicConfig(level=logging.DEBUG)

def createKernelSpecIfNeeded(kernelName):
    try:
        km = KernelManager(kernel_name=kernelName)
        km.kernel_spec
        return None
    except NoSuchKernel:
        sparkHome = os.environ["SPARK_HOME"]
        overrides={
            "argv": [
                "python",
                "-m",
                "ipykernel",
                "-f",
                "{connection_file}"
            ],
            "env": {
                "SCALA_HOME": "{0}".format(os.environ["SCALA_HOME"]),
                "SPARK_HOME": "{0}".format(sparkHome),
                "PYTHONPATH": "{0}/python/:{0}/python/lib/py4j-0.9-src.zip".format(sparkHome),
                "PYTHONSTARTUP": "{0}/python/pyspark/shell.py".format(sparkHome),
                "PYSPARK_SUBMIT_ARGS": "--driver-class-path {0}/data/libs/* --master local[10] pyspark-shell".format(os.environ.get("PIXIEDUST_HOME", os.path.expanduser('~'))),
                "SPARK_DRIVER_MEMORY":"10G",
                "SPARK_LOCAL_IP":"127.0.0.1"
            }
        }
        path = write_kernel_spec(overrides=overrides)
        dest = KernelSpecManager().install_kernel_spec(path, kernel_name=kernelName, user=True)
        # cleanup afterward
        shutil.rmtree(path)
        return dest

class RestartKernelException(Exception):
    pass

class CompareOutputException(Exception):
    pass

class PixieDustTestExecutePreprocessor( ExecutePreprocessor ):
    def preprocess_cell(self, cell, resources, cell_index):
        beforeOutputs = cell.outputs
        skipCompareOutput = "#SKIP_COMPARE_OUTPUT" in cell.source
        try:
            cell, resources = super(PixieDustTestExecutePreprocessor, self).preprocess_cell(cell, resources, cell_index)
            for output in cell.outputs:
                if "text" in output and "restart kernel" in output["text"].lower():
                    raise RestartKernelException()
            if not skipCompareOutput:
                self.compareOutputs(beforeOutputs, cell.outputs)
            return cell, resources
        except CellExecutionError:
            cell.source="%pixiedustLog -l debug"
            cell, resources = super(PixieDustTestExecutePreprocessor, self).preprocess_cell(cell, resources, cell_index)
            print("An error occurred executing the last cell. Fetching pixiedust log...")
            if len(cell.outputs) > 0 and "text" in cell.outputs[0]:
                print(cell.outputs[0].text)
            else:
                print("Pixiedust Log is empty")
            raise

    def compareOutputs(self, beforeOutputs, afterOutputs):
        #filter transient data from afterOutputs
        def filterOutput(output):
            return "data" in output and "application/javascript" in output["data"]

        afterOutputs = [output for output in afterOutputs if not filterOutput(output)]

        if ( len(beforeOutputs) != len(afterOutputs)):
            raise CompareOutputException("Output do not match. Expected {0} got {1}".format(beforeOutputs, afterOutputs))

        for beforeOutput, afterOutput in list(zip(beforeOutputs,afterOutputs)):
            if "output_type" in beforeOutput and beforeOutput["output_type"] != "execute_result":
                if len(beforeOutput) != len(afterOutput):
                    raise CompareOutputException("Output do not match. Expected {0} got {1}".format(beforeOutputs, afterOutputs))
                skip = ["execution_count"]
                for key in beforeOutput:
                    if beforeOutput[key] != afterOutput[key] and key not in skip:
                        raise CompareOutputException("Output do not match for {0}. Expected {1} got {2}".format(key, beforeOutput, afterOutput))

def runNotebook(path):
    ep = PixieDustTestExecutePreprocessor(timeout=3600, kernel_name= __TEST_KERNEL_NAME__)
    nb=nbformat.read(path, as_version=4)
    #set the kernel name to test
    nb.metadata.kernelspec.name=__TEST_KERNEL_NAME__
    if "pixiedust_test" in nb.metadata:
        testMeta = nb.metadata["pixiedust_test"]
        skipVersions = testMeta.get("skipPython",[])
        for skipVersion in skipVersions:
            skipVersion = int(float(skipVersion))
            if skipVersion == sys.version_info.major:
                print("Skipping processing of notebook {0} based on pixiedust_test metadata".format(path))
                return
    try:
        ep.preprocess(nb, {'metadata':{'path': os.path.dirname(path)}})
    finally:
        dir = os.environ.get("PIXIEDUST_TEST_OUTPUT", os.path.expanduser('~') + "/pixiedust") + "/tests"
        if not os.path.exists(dir):
            os.makedirs( dir )
        nbformat.write(nb, dir + "/" + os.path.basename(path) + ".out")

if __name__ == '__main__':
    if "PIXIEDUST_HOME" in os.environ:
        print("Using PIXIEDUST_HOME: ", os.environ["PIXIEDUST_HOME"])
    kernelPath = createKernelSpecIfNeeded(__TEST_KERNEL_NAME__)
    try:
        inputDir = os.environ.get("PIXIEDUST_TEST_INPUT", './tests')
        for path in os.listdir( inputDir ):
            if path.endswith(".ipynb"):
                print("Processing notebook {0}".format(path))
                processed = False
                count = 0
                while (not processed and count < 10 ):
                    try:
                        processed = True
                        count += 1
                        runNotebook(inputDir + "/" + path)
                    except RestartKernelException:
                        print("restarting kernel...")
                        processed = False
    finally:
        if kernelPath:
            shutil.rmtree(kernelPath)

        #clean up PIXIEDUST_HOME if provided
        def rmTree(path):
            if os.path.exists(path):
                shutil.rmtree(path)
        def rmFile(path):
            if os.path.exists(path):
                os.remove(path)
        if "PIXIEDUST_HOME" in os.environ:
            rmTree(os.environ["PIXIEDUST_HOME"] + "/data/libs")
            rmTree(os.environ["PIXIEDUST_HOME"] + "/pixiedust")
            rmFile(os.environ["PIXIEDUST_HOME"] + "/pixiedust.db")