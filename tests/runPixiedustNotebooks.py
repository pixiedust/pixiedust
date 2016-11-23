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
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

def runNotebook(path):
    ep = ExecutePreprocessor(timeout=3600, kernel_name= 'python2.7')
    nb=nbformat.read("./tests/" + path, as_version=4)

    try:
        ep.preprocess(nb, {'metadata':{'path': './tests/'}})
    except:
        print("Error executing notebook")
        raise
    else:
        pass
    finally:
        nbformat.write(nb, path + ".out")

if __name__ == '__main__':
    for path in os.listdir('./tests'):
        if path.endswith(".ipynb"):
            print("./tests/" + path)
            runNotebook(path)