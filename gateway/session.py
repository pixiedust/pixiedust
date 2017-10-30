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
import time
import uuid
from traitlets import Int
from traitlets.config.configurable import SingletonConfigurable
from tornado.ioloop import PeriodicCallback
from tornado.log import app_log
from .pixieGatewayApp import PixieGatewayApp
from .managedClient import ManagedClientPool

class Session(object):
    def __init__(self, session_id):
        self.session_id = session_id
        self.touch()
        self.run_ids = {}

    @property
    def namespace(self):
        return "inst_{}".format(self.session_id.replace('-', '_'))

    def getInstanceName(self, clazz):
        return "{}_{}".format(self.namespace, clazz.replace('.', '_'))

    def touch(self):
        """
        Update the last access time
        """
        self.last_accessed = round(time.time()*1000)

    def get_users_stats(self, mc_id):
        count = 0
        for managed_client in list(set(self.run_ids.values())):
            if managed_client.kernel_id == mc_id:
                count += 1
        return {"count": count}

    def shutdown(self):
        """
        Last chance to clean up before deleting the session
        remove all existing pixieapps for this session
        """
        print("Shutting down runs: {} Namespace: {}".format(self.run_ids, self.namespace))
        def done(future):
            print("Session successfully shut down: {}".format(future.result()))

        for managed_client in list(set(self.run_ids.values())):
            future = managed_client.execute_code("""
from pixiedust.utils.shellAccess import ShellAccess
from pixiedust.display.app import PixieDustApp
deleted_instances=[]
try:
    for key in list(ShellAccess.keys()):
        var = ShellAccess[key]
        if isinstance(var, PixieDustApp) and key.startswith("{}"):
            deleted_instances.append((key,var))
    for key, var in deleted_instances:
        print("Deleting instance {{}}".format(key))
        del var
except Exception as e:
    print("error", e)
    import traceback
    for line in traceback.format_stack():
        print(line.strip())
            """.format(self.namespace),
                lambda acc: "\n".join([msg['content']['text'] for msg in acc if msg['header']['msg_type'] == 'stream'])
            )
            future.add_done_callback(done)

    def _get_run_id_cookie_name(self, pixieapp_def):
        return "pd_runid_{}".format(pixieapp_def.name.replace(" ", "_"))

    def get_pixieapp_run_id(self, request_handler, pixieapp_def=None):
        if pixieapp_def is None:
            return None
        cookie_name = self._get_run_id_cookie_name(pixieapp_def)
        cookie = request_handler.get_secure_cookie(cookie_name)
        if cookie is None and hasattr(request_handler, cookie_name):
            cookie = getattr(request_handler, cookie_name)
        if cookie is None:
            cookie = str(uuid.uuid4())
            request_handler.set_secure_cookie(cookie_name, cookie)
            setattr(request_handler, cookie_name, cookie)
        elif hasattr(cookie, "decode"):
            cookie = cookie.decode("utf-8")
        return cookie

    def get_managed_client(self, request_handler, pixieapp_def=None, retry=False):
        if pixieapp_def is None:
            return ManagedClientPool.instance().get()

        run_id = self.get_pixieapp_run_id(request_handler, pixieapp_def)
        return self.get_managed_client_by_run_id(run_id, pixieapp_def, retry)

    def get_managed_client_by_run_id(self, run_id, pixieapp_def = None, retry=False):
        managed_client = self.run_ids[run_id] if run_id in self.run_ids else None
        if pixieapp_def is not None:
            if managed_client is None:
                managed_client = ManagedClientPool.instance().get(pixieapp_def)
                self.run_ids[run_id] = managed_client
            elif managed_client.get_app_stats(pixieapp_def) is None:
                del self.run_ids[run_id]
                if retry:
                    return self.get_managed_client_by_run_id(run_id, pixieapp_def, False)
                else:
                    raise Exception("Pixieapp has been restarted for this session. Please refresh the page")
        if managed_client is None:
            raise Exception("Invalid run_id: {} - {}".format(run_id, pixieapp_def))
        return managed_client

class SessionManager(SingletonConfigurable):
    """
    Manages all the user session. Todo: add persistent storage
    """

    session_timeout = Int(default_value=30*60, allow_none=True, config=True,
                          help="""Path containing the notebook with Runnable PixieApp""")

    def __init__(self, **kwargs):
        kwargs['parent'] = PixieGatewayApp.instance()
        super(SessionManager, self).__init__(**kwargs)
        self.session_map = {}
        self.session_validation_callback = PeriodicCallback(self.validate_sessions, 10 * 1000)
        self.session_validation_callback.start()

    def shutdown(self):
        self.session_validation_callback.stop()

    def get_users_stats(self, mc_id):
        count = 0
        for session in list(self.session_map.values()):
            count += session.get_users_stats(mc_id)['count']
        return {"count": count}

    def validate_sessions(self):
        current_time = round(time.time()*1000)
        for key,session in list(self.session_map.items()):
            if current_time - session.last_accessed > self.session_timeout*1000:
                app_log.debug("Stale session, deleting")
                session.shutdown()
                del self.session_map[key]

    def get_session(self, request_handler):
        session_id = request_handler.get_secure_cookie("pd_session_id")
        session = self.session_map.get(session_id.decode("utf-8")) if session_id is not None else None
        if session is None:
            app_log.debug("no session present, creating one")
            session_id = str(uuid.uuid4())
            request_handler.set_secure_cookie("pd_session_id", session_id)
            session = self.session_map[session_id] = Session(session_id)

        session.touch()
        return session
