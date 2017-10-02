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

class Session(object):
    def __init__(self, session_id):
        self.session_id = session_id
        self.touch()

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

    def validate_sessions(self):
        current_time = round(time.time()*1000)
        for key,session in list(self.session_map.items()):
            if current_time - session.last_accessed > self.session_timeout*1000:
                app_log.debug("Stale session, deleting")
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
