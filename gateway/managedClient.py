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
import json
from datetime import datetime
from tornado import locks
from tornado.concurrent import Future

from .pixieGatewayApp import PixieGatewayApp

class ManagedClient(object):
    """
    Managed access to a kernel client
    """
    def __init__(self, kernel_manager):
        kernel_id = kernel_manager.start_kernel()
        kernel = kernel_manager.get_kernel(kernel_id.result())

        self.kernel_client = kernel.client()
        self.kernel_client.session = type(self.kernel_client.session)(
            config=kernel.session.config,
            key=kernel.session.key,
        )
        self.iopub = kernel_manager.connect_iopub(kernel_id.result())

        # Start channels and wait for ready
        self.kernel_client.start_channels()
        self.kernel_client.wait_for_ready()
        print("kernel client initialized")

        self.lock = locks.Lock()

        #Initialize PixieDust
        self.execute_code("""
import pixiedust
from pixiedust.display.app import pixieapp
class Customizer():
    def customizeOptions(self, options):
        options.update( {'cell_id': 'dummy', 'showchrome':'false', 'gateway':'true'})
        options.update( {'nostore_pixiedust': 'true'})
pixieapp.pixieAppRunCustomizer = Customizer()
            """)

    def _date_json_serializer(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat().replace('+00:00', 'Z')
        raise TypeError("{} is not JSON serializable".format(obj))

    def _result_extractor(self, result_accumulator):
        return json.dumps(result_accumulator, default=self._date_json_serializer)

    def execute_code(self, code, result_extractor = None):
        """
        Asynchronously execute the given code using the underlying managed kernel client
        Note: this method is not synchronized, it is the responsibility of the caller to synchronize using the lock member variable
        e.g.
            with (yield managed_client.lock.acquire()):
                yield managed_client.execute_code( code )

        Parameters
        ----------
        code : String
            Python code to be executed

        result_extractor : function [Optional]
            Called when the code has finished executing to extract the results into the returned Future

        Returns
        -------
        Future
        
        """
        if result_extractor is None:
            result_extractor = self._result_extractor
        code = PixieGatewayApp.instance().prepend_execute_code + "\n" + code
        print("Executing Code: {}".format(code))
        future = Future()
        parent_header = self.kernel_client.execute(code)
        print("parent_header: {}".format(parent_header))
        result_accumulator = []
        def on_reply(msgList):
            session = type(self.kernel_client.session)(
                config=self.kernel_client.session.config,
                key=self.kernel_client.session.key,
            )
            _, msgList = session.feed_identities(msgList)
            msg = session.deserialize(msgList)
            if 'msg_id' in msg['parent_header'] and msg['parent_header']['msg_id'] == parent_header:
                if not future.done():
                    if "channel" not in msg:
                        msg["channel"] = "iopub"
                    result_accumulator.append(msg)
                    # Complete the future on idle status
                    if msg['header']['msg_type'] == 'status' and msg['content']['execution_state'] == 'idle':
                        future.set_result(result_extractor( result_accumulator ))
            else:
                print("Got an orphan message {}".format(msg))

        self.iopub.on_recv(on_reply)
        return future