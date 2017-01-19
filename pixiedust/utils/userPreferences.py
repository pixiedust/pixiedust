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

from .storage import *

USER_PREFERENCES_TBL_NAME="USER_PREFERENCES"

class __UserPreferences(Storage):
    def __init__(self):
        self._initTable( USER_PREFERENCES_TBL_NAME,
        '''
            PREF_KEY     TEXT  NOT NULL,
            PREF_VALUE   TEXT  NOT NULL,
            PRIMARY KEY (PREF_KEY)
        ''')

userPrefStorage = __UserPreferences()

def getUserPreference(prefKey, defaultValue=None):
    retValue = userPrefStorage.fetchOne("""
            SELECT * from {0} WHERE PREF_KEY='{1}'
        """.format(USER_PREFERENCES_TBL_NAME,prefKey), 
        lambda row: row["PREF_VALUE"]
    )
    return defaultValue if retValue is None else retValue

def setUserPreference(prefKey, prefValue):
    if getUserPreference(prefKey) is not None:
        userPrefStorage.update("""
            UPDATE {0} SET PREF_VALUE='{2}' WHERE PREF_KEY = '{1}'
        """.format(USER_PREFERENCES_TBL_NAME,prefKey, prefValue))
    else:
        userPrefStorage.insert("""
            INSERT INTO {0} (PREF_KEY, PREF_VALUE)
            VALUES ('{1}','{2}')
        """.format(USER_PREFERENCES_TBL_NAME, prefKey,prefValue))
