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
import re
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert.preprocessors.execute import CellExecutionError
import logging
from ipykernel.kernelspec import KernelSpecManager, write_kernel_spec
from jupyter_client.manager import KernelManager
from jupyter_client.kernelspec import NoSuchKernel
import shutil
from difflib import SequenceMatcher
from optparse import OptionParser

__TEST_KERNEL_NAME__ = "PixiedustTravisTest"

if "debug" in os.environ:
    logging.basicConfig(level=logging.DEBUG)

if "compareratio" in os.environ:
    try:
        compareRatio = float(os.environ["compareratio"])
    except:
        compareRatio = 0.98
else:
    compareRatio = 0.98

def createKernelSpecIfNeeded(kernelName, useSpark):
    try:
        km = KernelManager(kernel_name=kernelName)
        km.kernel_spec
        return None
    except NoSuchKernel:
        print("Creating new Kernel {} target: {}".format(kernelName, useSpark) )
        if useSpark:
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
        else:
            overrides={
                "argv": [
                    "python",
                    "-m",
                    "ipykernel",
                    "-f",
                    "{connection_file}"
                ],
                "env": {
                    "PIXIEDUST_HOME": os.environ.get("PIXIEDUST_HOME", os.path.expanduser('~'))
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
    def skipCell(self, cell):
        m = re.search("#TARGET=(.*)", cell.source, re.IGNORECASE)
        if m is not None:
            return (m.group(1).lower() == "spark") != self.useSpark
        return False

    def preprocess_cell(self, cell, resources, cell_index):
        if self.skipCell(cell):
            return cell, resources
        beforeOutputs = cell.outputs
        skipCompareOutput = "#SKIP_COMPARE_OUTPUT" in cell.source
        pixiedustDisplay = "display(" in cell.source
        try:
            logging.debug("Processing cell:\r\n{0}".format(cell.source))
            cell, resources = super(PixieDustTestExecutePreprocessor, self).preprocess_cell(cell, resources, cell_index)
            for output in cell.outputs:
                if "text" in output and "restart kernel" in output["text"].lower():
                    raise RestartKernelException()
            if not skipCompareOutput:
                if not pixiedustDisplay:
                    self.compareOutputs(beforeOutputs, cell.outputs, cell.source)
                else:
                    self.compareOutputs(beforeOutputs, cell.outputs, cell.source, True)
            return cell, resources
        except Exception as e:
            if isinstance(e, CellExecutionError):
                for output in cell.outputs:
                    logging.warn("Output Error is {}".format(output))
            cell.source="%pixiedustLog -l debug"
            cell, resources = super(PixieDustTestExecutePreprocessor, self).preprocess_cell(cell, resources, cell_index)
            logging.error("An error occurred executing the cell:\r\n{0}".format(cell.source))
            logging.info("Fetching pixiedust log...")
            if len(cell.outputs) > 0 and "text" in cell.outputs[0]:
                logging.warn(cell.outputs[0].text)
            else:
                logging.warn("Pixiedust Log is empty")
            raise

    def compareOutputs(self, beforeOutputs, afterOutputs, cellsource, useRatio=False):
        #return a measure of the sequences similarity as a float in the range [0, 1]
        seqmatcher = SequenceMatcher(None, '', '')

        #filter transient data from output
        def filterOutput(output):
            return "data" in output and "application/javascript" in output["data"]
            
        afterOutputs = [output for output in afterOutputs if not filterOutput(output)]

        if ( len(beforeOutputs) != len(afterOutputs)):
            logging.debug("Outputs do not match \r\nExpected:\r\n {0} \r\n\r\nActual:\r\n {1}".format(beforeOutputs, afterOutputs))
            raise CompareOutputException("Outputs do not match for cell:\r\n{0}".format(cellsource))

        for beforeOutput, afterOutput in list(zip(beforeOutputs,afterOutputs)):
            if "output_type" in beforeOutput and beforeOutput["output_type"] != "execute_result":
                if len(beforeOutput) != len(afterOutput):
                    logging.debug("output_type does not match \r\nExpected:\r\n {0} \r\n\r\nActual:\r\n {1}".format(beforeOutputs, afterOutputs))
                    raise CompareOutputException("output_type does not match for cell:\r\n{0}".format(cellsource))
                skip = ["execution_count"]
                expected = 0
                actual = 0
                longest = 0
                for key in beforeOutput:
                    if key not in skip:
                        before = str(beforeOutput[key])
                        after = str(afterOutput[key])
                        if useRatio:
                            seqmatcher.set_seqs(before, after)
                            expected = len(before)
                            actual = len(after)
                            ratio = seqmatcher.quick_ratio()
                            logging.info("expected_length: {0}, actual_length: {1}, sequence_ratio: {2}".format(expected, actual, ratio))
                            if ratio < compareRatio:
                                logging.debug("output_type ({0}) below ratio ({1}) threshold \r\nExpected:\r\n {2} \r\n\r\nActual:\r\n {3}".format(key, ratio, before, after))
                                raise CompareOutputException("output_type ({0}) below ratio ({1}) threshold for cell:\r\n{2}".format(key, ratio, cellsource))
                        elif beforeOutput[key] != afterOutput[key]:
                            logging.debug("output_type ({0}) does not match \r\nExpected:\r\n {1} \r\n\r\nActual:\r\n {2}".format(key, before, after))
                            raise CompareOutputException("output_type ({0}) does not match for cell:\r\n{1}".format(key, cellsource))

def runNotebook(path, useSpark):
    ep = PixieDustTestExecutePreprocessor(timeout=3600, kernel_name= __TEST_KERNEL_NAME__)
    ep.useSpark = useSpark
    nb=nbformat.read(path, as_version=4)
    #set the kernel name to test
    nb.metadata.kernelspec.name=__TEST_KERNEL_NAME__
    if "pixiedust_test" in nb.metadata:
        testMeta = nb.metadata["pixiedust_test"]
        targetKernel = testMeta.get("target")
        if targetKernel is not None and (targetKernel.lower() == "spark") != useSpark:
            logging.warn("Skipping processing of notebook {0} based on pixiedust_test metadata".format(path))
            return
        skipVersions = testMeta.get("skipPython",[])
        for skipVersion in skipVersions:
            skipVersion = int(float(skipVersion))
            if skipVersion == sys.version_info.major:
                logging.warn("Skipping processing of notebook {0} based on pixiedust_test metadata".format(path))
                return
    try:
        ep.preprocess(nb, {'metadata':{'path': os.path.dirname(path)}})
    finally:
        dir = os.environ.get("PIXIEDUST_TEST_OUTPUT", os.path.expanduser('~') + "/pixiedust") + "/tests"
        if not os.path.exists(dir):
            os.makedirs( dir )
        nbformat.write(nb, dir + "/" + os.path.basename(path) + ".out")

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-t", "--target", dest="target", default="spark", help="target kernel: spark or plain")

    (options, args) = parser.parse_args()
    useSpark = options.target == "spark"
    print("Starting Test Suite with target: {}".format(options.target) )
    if "PIXIEDUST_HOME" in os.environ:
        print("Using PIXIEDUST_HOME: ", os.environ["PIXIEDUST_HOME"])
    kernelPath = createKernelSpecIfNeeded(__TEST_KERNEL_NAME__, useSpark)
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
                        runNotebook(inputDir + "/" + path, useSpark)
                    except RestartKernelException:
                        logging.warn("Restarting kernel...")
                        processed = False
                    except:
                        logging.warn("Fatal Error in Notebook {}.".format(path))
                        raise
                print("Finished processing notebook {0}".format(path))
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