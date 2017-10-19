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
from pixiedust.utils.storage import Storage
import uuid

class ChartStorage(Storage):
    CHARTS_TBL_NAME="CHARTS"
    def __init__(self):
        self._initTable( ChartStorage.CHARTS_TBL_NAME,
        '''
            CHARTID        TEXT  NOT NULL PRIMARY KEY,
            AUTHOR         TEXT  NOT NULL,
            DATE           DATETIME  NOT NULL,
            DESCRIPTION    TEXT,
            CONTENT        BLOB
        ''')

    def store_chart(self, payload):
        chart_id = str(uuid.uuid4())
        print(chart_id.__class__)
        self.insert("""
            INSERT INTO {0} (CHARTID,AUTHOR,DATE,DESCRIPTION,CONTENT)
            VALUES (?,?,CURRENT_TIMESTAMP,?,?)
        """.format(ChartStorage.CHARTS_TBL_NAME), (
            chart_id,
            "username",
            payload.get("description", ""),
            payload['chart']
        ))
        #return the chart_model for this newly stored chart
        return self.get_chart(chart_id)

    def get_chart(self, chart_id):
        return self.fetchOne(
            """SELECT * from {0} WHERE CHARTID='{1}'""".format(
                ChartStorage.CHARTS_TBL_NAME, chart_id
            )
        )

    def delete_chart(self, chart_id):
        rows_deleted = self.delete(
            """DELETE FROM {0} WHERE CHARTID='{1}'""".format(
                ChartStorage.CHARTS_TBL_NAME, chart_id
            )
        )
        print("Row Deleted: {}".format(rows_deleted))
        return rows_deleted

    def list_charts(self):
        def walker(row):
            print(row['CHARTID'])
        self.execute("""
                SELECT * FROM {0}
            """.format(ChartStorage.CHARTS_TBL_NAME),
            walker
        )

chart_storage = ChartStorage()
