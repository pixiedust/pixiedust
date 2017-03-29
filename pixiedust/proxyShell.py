# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2017
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
import sys
import json

from ipykernel.jsonutil import json_clean, encode_images

from IPython.core.interactiveshell import (
    InteractiveShell, InteractiveShellABC
)

from IPython.core.displaypub import DisplayPublisher
from traitlets import Type

class ProxyShellCaptureOutput(object):
    def formatMessage(self, message):
        try:
            jsMsg = eval(message)
            return json.dumps(jsMsg)
        except Exception as e:
            return """{{"text/plain":"{0}"}}""".format(message)

    def write(self, message):
        try:
            self.sys_stdout.write( message )
        except Exception as e:
            self.sys_stdout.write("got error" + str(e))
    
    def __enter__(self):       
        self.sys_stdout = sys.stdout
        self.sys_stderr = sys.stderr
        
        sys.stdout = self
        sys.stderr = self
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_value is not None:
            print("exc_type", exc_type)
            print("exc_value", str(exc_value))
            print("traceback", str(traceback))
        sys.stdout = self.sys_stdout
        sys.stderr = self.sys_stderr

class ProxyDisplayPublisher(DisplayPublisher):
    def publish(self, data, metadata=None, source=None):
        if not isinstance(data, dict):
            raise TypeError('data must be a dict, got: %r' % data)
        if metadata is not None and not isinstance(metadata, dict):
            raise TypeError('metadata must be a dict, got: %r' % data)
        content = {}
        content['data'] = encode_images(data)
        content['metadata'] = metadata
        print(json.dumps(json_clean(content)))

class ProxyInteractiveShell(InteractiveShell):
    display_pub_class = Type(ProxyDisplayPublisher)
    def enable_gui(gui, kernel=None):
        pass

InteractiveShellABC.register(ProxyInteractiveShell)