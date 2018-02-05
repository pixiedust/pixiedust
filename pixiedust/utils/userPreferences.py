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

from six import iteritems
from .storage import *

USER_PREFERENCES_TBL_NAME = "USER_PREFERENCES"

class __UserPreferences(Storage):
    def __init__(self):
        self._initTable(USER_PREFERENCES_TBL_NAME,
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
        """.format(USER_PREFERENCES_TBL_NAME, prefKey, prefValue))

class user_preferences:
    """
    Decorator for classed to automatically add fields getter and setter that are persisted
    in the pixiedust database
    example usage:
    @user_preferences(key1="value1", key2="value2")
    class Test():
        pass

    t = Test()
    print(t.key1)
    t.key1 = "value11"
    print(t.key1)
    """
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, cls):
        for key, default_value in iteritems(self.kwargs):
            def create_property_fn(key, default_value):
                prop_name = "_" + key
                preference_key_name = "{}_{}".format(cls.__name__, key)
                def prop_get(self):
                    if not hasattr(self, prop_name):
                        setattr(self, prop_name, getUserPreference(preference_key_name, default_value))
                    return getattr(self, prop_name)
                def prop_set(self, value):
                    setUserPreference(preference_key_name, value)
                    setattr(self, prop_name, value)
                setattr(cls, key, property(prop_get, prop_set))
            create_property_fn(key, default_value)
        return cls
