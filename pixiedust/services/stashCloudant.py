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

from ..display.display import Display
from .serviceManager import *
import time
import requests
import json

CLOUDANT_CONN_TYPE = "cloudant"

class StashCloudantHandler(Display):
    def doRender(self, handlerId):
        entity=self.entity

        dbName = self.options.get("dbName", "dataframe-"+time.strftime('%Y%m%d-%H%M%S'))
        connectionName=self.options.get("connection")
        if connectionName is None:
            self._addHTMLTemplate("stashCloudant.html",dbName=dbName,connections=getConnections(CLOUDANT_CONN_TYPE))
        else:
            #first create the stash db
            connection = getConnection(CLOUDANT_CONN_TYPE, connectionName)
            if not connection:
                raise Exception("Unable to resolve connection {0}".format(connectionName))
            payload = json.loads( connection["PAYLOAD"])
            credentials=payload["credentials"]
            r = requests.put( credentials["url"] + "/" + dbName )
            if ( r.status_code != 200 and r.status_code != 201 ):
                print("Unable to create db ({0}) for connection ({1}): {2}".format(dbName, connectionName, str(r.content)))
            else:
                self.entity.write.format("com.cloudant.spark")\
                    .option("cloudant.host", credentials["host"])\
                    .option("cloudant.username",credentials["username"])\
                    .option("cloudant.password",credentials["password"])\
                    .option("createDBOnSave","true")\
                    .save(dbName)
                print("""Successfully stashed your data: <a target='_blank' href='{0}/{1}'>{1}</a>""".format(credentials["url"],dbName))