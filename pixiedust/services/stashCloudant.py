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
import time
import requests

class StashCloudantHandler(Display):
    def doRender(self, handlerId):
        entity=self.entity

        dbName = self.options.get("dbName", "dataframe-"+time.strftime('%m%d%Y-%H%M'))
        doStash=self.options.get("doStash")
        if doStash is None:
            self._addHTMLTemplate("stashCloudant.html",dbName=dbName)
        else:
            #first create the stash db
            r = requests.put("http://dtaieb:password@127.0.0.1:5984/" + dbName )
            if ( r.status_code != 200 and r.status_code != 201 ):
                print("Unable to create db: " + str(r.content) )
            else:
                self.entity.write.format("com.cloudant.spark")\
                    .option("cloudant.host", "http://127.0.0.1:5984")\
                    .option("cloudant.username","dtaieb")\
                    .option("cloudant.password","password")\
                    .option("createDBOnSave","true")\
                    .save(dbName)
                print("""Successfully stashed your data: <a target='_blank' href='http://127.0.0.1:5984/{0}'>{0}</a>""".format(dbName))