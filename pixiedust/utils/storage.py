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

import sqlite3
import os

import json
import sys
import time
from pixiedust.utils.constants import PIXIEDUST_REPO_URL
from pkg_resources import get_distribution
from re import search
from requests import post
from os import environ as env
from pixiedust.utils.printEx import *

from . import pdLogging
logger = pdLogging.getPixiedustLogger()
getLogger = pdLogging.getLogger

myLogger = getLogger(__name__)

__all__ = ['Storage']

SQLITE_DB_NAME = os.environ.get('PIXIEDUST_DB_NAME', 'pixiedust.db')
SQLITE_DB_NAME_PATH = os.environ.get("PIXIEDUST_HOME", os.path.expanduser('~')) + "/" + SQLITE_DB_NAME

if not os.path.exists(os.path.dirname(SQLITE_DB_NAME_PATH)):
    os.makedirs(os.path.dirname(SQLITE_DB_NAME_PATH))

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

    _trackDeployment()

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
            return cursor.rowcount
        finally:
            if cursor is not None:
                cursor.close()

    def insert(self, sqlQuery, arguments=None):
        if arguments is not None:
            _conn.execute(sqlQuery, arguments)
        else:
            _conn.execute(sqlQuery)
        _conn.commit()

    def update(self, sqlQuery):
        _conn.execute(sqlQuery)
        _conn.commit()

DEPLOYMENT_TRACKER_TBL_NAME = "VERSION_TRACKER"

class __DeploymentTrackerStorage(Storage):
    def __init__(self):
        self._initTable(DEPLOYMENT_TRACKER_TBL_NAME,"VERSION TEXT NOT NULL")

def _trackDeployment():
    deploymenTrackerStorage = __DeploymentTrackerStorage()
    row = deploymenTrackerStorage.fetchOne("SELECT * FROM {0}".format(DEPLOYMENT_TRACKER_TBL_NAME));
    if row is None:
        _trackDeploymentIfVersionChange(deploymenTrackerStorage, None)
    else:
        _trackDeploymentIfVersionChange(deploymenTrackerStorage, row["VERSION"])

def _trackDeploymentIfVersionChange(deploymenTrackerStorage, existingVersion):
    # Get version and repository URL from 'setup.py'
    version = None
    repo_url = None
    try:
        app = get_distribution("pixiedust")
        version = app.version
        repo_url = PIXIEDUST_REPO_URL
        notebook_tenant_id = os.environ.get("NOTEBOOK_TENANT_ID")
        notebook_kernel = os.environ.get("NOTEBOOK_KERNEL")
        # save last tracked version in the db
        if existingVersion is None:
            deploymenTrackerStorage.insert("INSERT INTO {0} (VERSION) VALUES ('{1}')".format(DEPLOYMENT_TRACKER_TBL_NAME,version))
        else:
            deploymenTrackerStorage.update("UPDATE {0} SET VERSION='{1}'".format(DEPLOYMENT_TRACKER_TBL_NAME,version))
        # if version has changed then track with deployment tracker
        if existingVersion is None or existingVersion != version:
            myLogger.info("Change in version detected: {0} -> {1}.".format(existingVersion,version))
            if existingVersion is None:
                printWithLogo("Pixiedust version {0}".format(version))
            else:
                printWithLogo("Pixiedust version upgraded from {0} to {1}".format(existingVersion,version))
            # create dictionary and register
            event = dict()
            event['date_sent'] = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
            if version is not None:
                event['code_version'] = version
            if repo_url is not None:
                event['repository_url'] = repo_url
            if notebook_tenant_id is not None:
                event['notebook_tenant_id'] = notebook_tenant_id
            if notebook_kernel is not None:
                event['notebook_kernel'] = notebook_kernel
            event['runtime'] = 'python'
            # Create and format request to Deployment Tracker
            url = 'https://deployment-tracker.mybluemix.net/api/v1/track'
            headers = {'content-type': "application/json"}
            response = post(url, data=json.dumps(event), headers=headers)
        else:
            myLogger.info("No change in version: {0} -> {1}.".format(existingVersion,version))
            printWithLogo("Pixiedust version {0}".format(version)) 
    except:
        myLogger.error("Error registering with deployment tracker:\n" + str(sys.exc_info()[0]) + "\n" + str(sys.exc_info()[1]))