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

import hashlib
import json
import getpass
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

    def _tableExists(self, tableName):
        cursor=_conn.execute("""
            SELECT * FROM sqlite_master WHERE name ='{0}' and type='table';
        """.format(tableName))
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists

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

    def update(self, sqlQuery, arguments=None):
        if arguments is not None:
            _conn.execute(sqlQuery, arguments)
        else:
            _conn.execute(sqlQuery)
        _conn.commit()

PIXIEDUST_VERSION_TBL_NAME = "VERSION_TRACKER"
METRICS_TRACKER_TBL_NAME = "METRICS_TRACKER"

class __DeploymentTrackerStorage(Storage):
    def __init__(self):
        self._initTable(PIXIEDUST_VERSION_TBL_NAME,"VERSION TEXT NOT NULL")

def _trackDeployment():
    deploymenTrackerStorage = __DeploymentTrackerStorage()
    doNotTrack = None
    lastVersionTracked = None
    # if the metrics tracker table does not exist then this represents a new install
    # we do not want to track the user until after they have a chance to opt out
    if not deploymenTrackerStorage._tableExists(METRICS_TRACKER_TBL_NAME):
        doNotTrack = True
        deploymenTrackerStorage._initTable(METRICS_TRACKER_TBL_NAME,"LAST_VERSION_TRACKED TEXT NULL, OPT_OUT BOOLEAN NOT NULL")
        deploymenTrackerStorage.insert("INSERT INTO {0} (OPT_OUT) VALUES ({1})".format(METRICS_TRACKER_TBL_NAME,0))
        print("""
Share anonymous install statistics? (opt-out instructions)

PixieDust will record metadata on its environment the next time the package is installed or updated. The data is anonymized and aggregated to help plan for future releases, and records only the following values:

{
   "data_sent": currentDate,
   "runtime": "python",
   "application_version": currentPixiedustVersion,
   "space_id": nonIdentifyingUniqueId,
   "config": {
       "repository_id": "https://github.com/ibm-watson-data-lab/pixiedust",
       "target_runtimes": ["Data Science Experience"],
       "event_id": "web",
       "event_organizer": "dev-journeys"
   }
}
You can opt out by calling pixiedust.optOut() in a new cell.""")
    else:
        row = deploymenTrackerStorage.fetchOne("SELECT * FROM {0}".format(METRICS_TRACKER_TBL_NAME));
        if row is None:
            deploymenTrackerStorage.insert("INSERT INTO {0} (OPT_OUT) VALUES ({2})".format(METRICS_TRACKER_TBL_NAME,0))
            doNotTrack = False
            lastVersionTracked = None
        else:
            doNotTrack = row["OPT_OUT"] == 1
            lastVersionTracked = row["LAST_VERSION_TRACKED"]

    row = deploymenTrackerStorage.fetchOne("SELECT * FROM {0}".format(PIXIEDUST_VERSION_TBL_NAME));
    if row is None:
        _updateVersionAndTrackDeployment(deploymenTrackerStorage, None, lastVersionTracked, doNotTrack)
    else:
        _updateVersionAndTrackDeployment(deploymenTrackerStorage, row["VERSION"], lastVersionTracked, doNotTrack)

def _updateVersionAndTrackDeployment(deploymenTrackerStorage, lastPixiedustVersion, lastVersionTracked, doNotTrack):
    # Get version and repository URL from 'setup.py'
    version = None
    try:
        app = get_distribution("pixiedust")
        version = app.version
        # save last tracked version in the db
        if lastPixiedustVersion is None:
            deploymenTrackerStorage.insert("INSERT INTO {0} (VERSION) VALUES ('{1}')".format(PIXIEDUST_VERSION_TBL_NAME,version))
        else:
            deploymenTrackerStorage.update("UPDATE {0} SET VERSION='{1}'".format(PIXIEDUST_VERSION_TBL_NAME,version))
        # if version has changed then track with deployment tracker
        if lastPixiedustVersion is None or lastPixiedustVersion != version:
            myLogger.info("Change in version detected: {0} -> {1}.".format(lastPixiedustVersion,version))
            if lastPixiedustVersion is None:
                printWithLogo("Pixiedust version {0}".format(version))
            else:
                printWithLogo("Pixiedust version upgraded from {0} to {1}".format(lastPixiedustVersion,version))
            # register
            if not doNotTrack:
                deploymenTrackerStorage.update("UPDATE {0} SET LAST_VERSION_TRACKED='{1}'".format(METRICS_TRACKER_TBL_NAME,version))
                track(version)
        else:
            myLogger.info("No change in version: {0} -> {1}.".format(lastPixiedustVersion,version))
            printWithLogo("Pixiedust version {0}".format(version))
            # if never tracked then track for the first time
            if lastVersionTracked is None and not doNotTrack:
                deploymenTrackerStorage.update("UPDATE {0} SET LAST_VERSION_TRACKED='{1}'".format(METRICS_TRACKER_TBL_NAME,version))
                track(version)
    except:
        myLogger.error("Error registering with deployment tracker:\n" + str(sys.exc_info()[0]) + "\n" + str(sys.exc_info()[1]))

def track(version):
    event = dict()
    event['date_sent'] = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
    event['runtime'] = 'python'
    if version is not None:
        event['application_version'] = version
    try:
        # a hashed value that uniquely identifies this user
        # no password or identifying information are tracked
        event['space_id'] = hashlib.md5(getpass.getuser()).hexdigest()
    except:
        pass
    event['config'] = {}
    event['config']['repository_id'] = PIXIEDUST_REPO_URL
    event['config']['target_runtimes'] = ['Data Science Experience']
    event['config']['event_id'] = 'web'
    event['config']['event_organizer'] = 'dev-journeys'
    url = 'https://metrics-tracker.mybluemix.net/api/v1/track'
    headers = {'content-type': "application/json"}
    try:
        response = post(url, data=json.dumps(event), headers=headers)
        myLogger.info('Anonymous install statistics collected.')
    except Exception as e:
        myLogger.error('Anonymous install statistics collection error: %s' % str(e))

def optOut():
    deploymenTrackerStorage = __DeploymentTrackerStorage()
    deploymenTrackerStorage.update("UPDATE {0} SET OPT_OUT={1}".format(METRICS_TRACKER_TBL_NAME,1))
    print("Pixiedust will not collect anonymous install statistics.")

def optIn():
    deploymenTrackerStorage = __DeploymentTrackerStorage()
    deploymenTrackerStorage.update("UPDATE {0} SET OPT_OUT={1}".format(METRICS_TRACKER_TBL_NAME,0))
    print("Pixiedust will collect anonymous install statistics. To opt out, call pixiedust.optOut() in a new cell.")