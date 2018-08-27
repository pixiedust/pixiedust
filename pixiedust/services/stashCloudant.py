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

from ..display.display import Display
from .serviceManager import *
import time
import requests
import json
from pixiedust.utils import Logger
from pixiedust.utils.shellAccess import ShellAccess
from pixiedust.utils.environment import Environment

CLOUDANT_CONN_TYPE = "cloudant"
@Logger()
class StashCloudantHandler(Display):
    def tuplize(self, connections):
        return [tuple(connections[i:i+2]) for i in range(0, len(connections), 2)]

    def doRender(self, handlerId):
        if self.options.get("nostore_listConnections"):
            return self._addHTMLTemplate("listConnections.html", connections=self.tuplize(getConnections(CLOUDANT_CONN_TYPE)) )

        config = ShellAccess.sc._conf.getAll()
        checks = ["spark-cloudant", "cloudant-spark"]
        sparkJars = [t[1] for t in config if t[0]=="spark.jars"]
        cond1 = any("spark.jars" in s for s in config) and any( c in s for s in sparkJars for c in checks)
        cond2 = any(c in s for s in Environment.javaClassPath.split(":") for c in checks)
        if not cond1 and not cond2:
            self._addHTML("<p>Please setup one time manual steps to configure stashing to Cloudant database at <a href=\"https://pixiedust.github.io/pixiedust/install.html#stash-to-cloudant\"  target=\"_blank\">https://pixiedust.github.io/pixiedust/install.html#stash-to-cloudant</a></p>")
            self.debug("Please setup one time manual steps to configure stashing to Cloudant database at https://pixiedust.github.io/pixiedust/install.html#stash-to-cloudant")
            self.debug("SparkContext conf:")
            self.debug(config)
            return
                    
        entity=self.entity

        dbName = self.options.get("nostore_dbName", "dataframe-"+time.strftime('%Y%m%d-%H%M%S'))
        connectionName=self.options.get("nostore_connection")
        if connectionName is None:
            self._addHTMLTemplate("stashCloudant.html",dbName=dbName,connType=CLOUDANT_CONN_TYPE, connections=self.tuplize(getConnections(CLOUDANT_CONN_TYPE)))
        else:
            #first create the stash db
            connection = getConnection(CLOUDANT_CONN_TYPE, connectionName)
            if not connection:
                raise Exception("Unable to resolve connection {0}".format(connectionName))
            payload = json.loads( connection["PAYLOAD"])
            credentials=payload["credentials"]
            self.debug("write to cloudant host {0}".format(credentials["host"]))
            format = self.entity.write.format("com.cloudant.spark")\
                .option("cloudant.host", credentials["host"])\
                .option("cloudant.username",credentials["username"])\
                .option("cloudant.password",credentials["password"])\
                .option("createDBOnSave","true")
            
            if "protocol" in credentials:
                format.option("cloudant.protocol", credentials["protocol"])
            
            format.save(dbName)
            self._addHTML("""<div>Successfully stashed your data: <a target='_blank' href='{0}/{1}'>{1}</a></div>""".format(credentials["url"],dbName))