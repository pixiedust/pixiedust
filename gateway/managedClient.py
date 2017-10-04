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
from six import iteritems
from tornado import locks, gen
from tornado.log import app_log
from tornado.concurrent import Future
from traitlets.config.configurable import SingletonConfigurable
from .pixieGatewayApp import PixieGatewayApp

class ManagedClient(object):
    """
    Managed access to a kernel client
    """
    def __init__(self, kernel_manager):
        self.kernel_manager = kernel_manager
        self.start()
        self.installed_modules = []
        self.stats = {}

    def get_running_stats(self, pixieapp_def, stat_name = None):
        if not pixieapp_def.name in self.stats or (stat_name is not None and stat_name not in self.stats[pixieapp_def.name]):
            return None
        return self.stats[pixieapp_def.name][stat_name] if stat_name is not None else self.stats[pixieapp_def.name]

    def set_running_stats(self, pixieapp_def, stat_name, stat_value):
        if not pixieapp_def.name in self.stats:
            self.stats[pixieapp_def.name] = {}

        self.stats[pixieapp_def.name][stat_name] = stat_value

    def start(self):
        self.kernel_id = self.kernel_manager.start_kernel().result()
        kernel = self.kernel_manager.get_kernel(self.kernel_id)

        self.kernel_client = kernel.client()
        self.kernel_client.session = type(self.kernel_client.session)(
            config=kernel.session.config,
            key=kernel.session.key
        )
        self.iopub = self.kernel_manager.connect_iopub(self.kernel_id)

        # Start channels and wait for ready
        self.kernel_client.start_channels()
        self.kernel_client.wait_for_ready()
        print("kernel client initialized")

        self.lock = locks.Lock()

        #Initialize PixieDust
        future = self.execute_code("""
import pixiedust
import pkg_resources
import json
from pixiedust.display.app import pixieapp
class Customizer():
    def __init__(self):
        self.gateway = 'true'
    def customizeOptions(self, options):
        options.update( {'cell_id': 'dummy', 'showchrome':'false', 'gateway':self.gateway})
        options.update( {'nostore_pixiedust': 'true'})
pixieapp.pixieAppRunCustomizer = Customizer()
print(json.dumps( {"installed_modules": list(pkg_resources.AvailableDistributions())} ))
            """, lambda acc: json.dumps([msg['content']['text'] for msg in acc if msg['header']['msg_type'] == 'stream'], default=self._date_json_serializer))
    
        def done(fut):
            results = json.loads(fut.result())
            for result in results:
                try:
                    val = json.loads(result)
                    if isinstance(val, dict) and "installed_modules" in val:
                        self.installed_modules = val["installed_modules"]
                        break
                except:
                    pass
            app_log.debug("Installed modules %s", self.installed_modules)
        future.add_done_callback(done)

    def shutdown(self):
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel(self.kernel_id, now=True)

    @gen.coroutine
    def install_dependencies(self, pixieapp_def, log_messages):
        restart = False
        for dep, info in [ (d,i) for d,i in iteritems(pixieapp_def.deps) if not any(a for a in [d,d.replace("-","_"),d.replace("_","-")] if a in self.installed_modules)]:
            log_messages.append("Installing module: {} from {}".format(dep, info))
            pip_dep = dep
            if info.get("install", None) is not None:
                pip_dep = info.get("install")
            yield self.execute_code("!pip install {}".format(pip_dep))
            restart = True
        raise gen.Return(restart)

    @gen.coroutine
    def on_publish(self, pixieapp_def, log_messages):
        future = Future()
        restart = yield self.install_dependencies(pixieapp_def, log_messages)
        if restart or self.get_running_stats(pixieapp_def) is not None:
            log_messages.append("Restarting kernel {}...".format(self.kernel_id))
            yield gen.maybe_future(self.restart())
            log_messages.append("Kernel successfully restarted...")
        future.set_result("OK")
        return future

    @gen.coroutine
    def restart(self):
        with (yield self.lock.acquire()):
            yield gen.maybe_future(self.shutdown())
            self.installed_modules = []
            self.stats = {}
            yield gen.maybe_future(self.start())

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
        app_log.debug("Executing Code: %s", code)
        future = Future()
        parent_header = self.kernel_client.execute(code)
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
                app_log.warning("Got an orphan message %s", msg)

        self.iopub.on_recv(on_reply)
        return future

class ManagedClientPool(SingletonConfigurable):
    """
    Orchestrates a Pool of ManagedClients, load-balancing based on user load
    """
    def __init__(self, kernel_manager, **kwargs):
        kwargs['parent'] = PixieGatewayApp.instance()
        super(ManagedClientPool, self).__init__(**kwargs)
        self.kernel_manager = kernel_manager
        self.managed_clients = []
        self.managed_clients.append(ManagedClient(kernel_manager))

    def shutdown(self):
        for managed_client in self.managed_clients:
            managed_client.shutdown()

    def on_publish(self, pixieapp_def, log_messages):
        #find all the affect clients
        try:
            log_messages.append("Validating Kernels for publishing...")
            return [managed_client.on_publish(pixieapp_def, log_messages) for managed_client in self.managed_clients]
        finally:
            log_messages.append("Done Validating Kernels...")

    def get(self):
        return self.managed_clients[0]
