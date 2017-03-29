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

from pixiedust.utils import Logger
from pixiedust.utils.storage import *
import json

CONNECTION_TBL_NAME = "service_connections"
VERSION = 1 

#global Storage
@Logger()
class __ServiceManagerStorage(Storage):
    def __init__(self):
        self._initTable( CONNECTION_TBL_NAME, 
        """
            NAME            TEXT NOT NULL,
            TYPE            TEXT NOT NULL,
            VERSION         INTEGER NOT NULL,
            PAYLOAD         TEXT  NOT NULL,
            PRIMARY KEY (NAME, TYPE)
        """)

    def getConnections(self, connectionType):
        return self.fetchMany("""
                SELECT * FROM {0} WHERE TYPE = '{1}'
            """.format(CONNECTION_TBL_NAME, connectionType),
            lambda row: json.loads(row["PAYLOAD"])
        )

    def getConnection(self, connectionType, connectionName, raw=True):
        row = self.fetchOne("""
            SELECT * FROM {0} WHERE NAME='{1}' AND TYPE='{2}'
        """.format(
                CONNECTION_TBL_NAME,
                connectionName,
                connectionType
            )
        )
        if row is None:
            raise Exception("Unable to find connection {0} with type {1}".format(connectionName, connectionType))

        return row if raw else json.loads(row['PAYLOAD'])

    def addConnection(self, connectionType, payload):
        self._validatePayload(payload)

        name = payload["name"]
        try:
            self.getConnection(connectionType, name )
            #already exist, update
            self.update("""
                UPDATE {0} SET PAYLOAD='{1}' WHERE NAME = '{2}' and TYPE='{3}'
            """.format(CONNECTION_TBL_NAME, json.dumps(payload), payload["name"], connectionType))
        except:
            #doesn't exist, try to insert
            self.insert("""
                INSERT INTO {0} (NAME, TYPE,VERSION,PAYLOAD)
                VALUES ('{1}','{2}','{3}','{4}')
            """.format(CONNECTION_TBL_NAME, payload["name"], connectionType, VERSION, json.dumps(payload)))

        return payload["name"]

    def _validatePayload(self, payload):
        if not "name" in payload:
            raise Exception("Missing field name")

    def deleteConnection(self, connectionType, connectionName):
        return self.delete("""
            DELETE FROM {0} WHERE NAME='{1}' AND TYPE='{2}'
        """.format(
                CONNECTION_TBL_NAME,
                connectionName,
                connectionType
            )
        )

__connectionsStorage = __ServiceManagerStorage()

#public CRUD APIs
def getConnections(connectionType):
    return __connectionsStorage.getConnections(connectionType)

def getConnection(connectionType, connectionName, raw=True):
    return __connectionsStorage.getConnection(connectionType, connectionName, raw=raw)

def addConnection(connectionType, payload):
    return __connectionsStorage.addConnection(connectionType, payload)

def deleteConnection(connectionType, connectionName):
    return __connectionsStorage.deleteConnection(connectionType, connectionName)