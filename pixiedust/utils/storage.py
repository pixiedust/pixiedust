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

import sqlite3
import os

__all__ = ['Storage']

SQLITE_DB_NAME = 'pixiedust.db'
SQLITE_DB_NAME_PATH = os.path.expanduser('~') + "/" + SQLITE_DB_NAME
#global connection
_conn = None

def _initStorage():
    def copyRename(oldName, newName):
        if os.path.isfile(oldName) and not os.path.isfile(newName):
            from shutil import copyfile
            copyfile(oldName, newName)
            os.rename(oldName, oldName + ".migrated")
            print("INFO: migrated pixiedust database")

    #if db already exist with old name, rename it now
    copyRename('spark.db', SQLITE_DB_NAME)
    copyRename(SQLITE_DB_NAME, SQLITE_DB_NAME_PATH)

    global _conn
    if not _conn:
        def _row_dict_factory(cursor,row):
            res={}
            for i,col in enumerate(cursor.description):
                res[col[0]]=row[i]
            return res
        _conn = sqlite3.connect(SQLITE_DB_NAME_PATH)
        _conn.row_factory=_row_dict_factory 
        print("Pixiedust database opened successfully")

"""
Encapsule access to data from the pixiedust database
including storage lifecycle e.g. schema definition and creation, cleanup, etc...
"""
class Storage(object):
    def __init__(self):
        pass

    def _initTable(self, tableName, schemaDef):
        cursor=_conn.execute("""
            SELECT * FROM sqlite_master WHERE name ='{0}' and type='table';
        """.format(tableName))
        if cursor.fetchone() is None:
            _conn.execute('''CREATE TABLE {0} ({1});'''.format(tableName, schemaDef))
            print("Table {0} created successfully".format(tableName))
        '''
        else:
            print("Deleting table")
            _conn.execute("""DROP TABLE {0}""".format(tableName))
        '''
        cursor.close()

    def fetchOne(self, sqlQuery, mapper=None):
        cursor=None
        try:
            cursor=_conn.execute(sqlQuery)
            row = cursor.fetchone()
            return row if row is None or mapper is None else mapper(row)
        finally:
            if cursor is not None:
                cursor.close()

    def fetchMany(self, sqlQuery, mapper=None):
        cursor=None
        try:
            cursor=_conn.execute(sqlQuery)
            results = cursor.fetchmany()
            ret = []
            while results:
                for row in results:
                    ret.append( row if mapper is None else mapper(row) )
                results = cursor.fetchmany()
            return ret
        finally:
            if cursor is not None:
                cursor.close()

    def execute(self, sqlQuery, handler):
        cursor=None
        try:
            cursor=_conn.execute(sqlQuery)
            results = cursor.fetchmany()
            while results:
                for row in results:
                    handler(row)
                results = cursor.fetchmany()
        finally:
            if cursor is not None:
                cursor.close()

    """Return the number of rows deleted"""
    def delete(self, sqlQuery):
        cursor = None
        try:
            cursor=_conn.execute(sqlQuery)
            _conn.commit()
            return _conn.total_changes
        finally:
            if cursor is not None:
                cursor.close()

    def insert(self, sqlQuery):
        _conn.execute(sqlQuery)
        _conn.commit()

