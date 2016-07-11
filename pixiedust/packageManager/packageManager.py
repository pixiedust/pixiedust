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

from __future__ import print_function
import sqlite3
import sys
import platform
import urllib
import os
from ..display.printEx import *
from maven import Artifact
from maven import downloader
from maven import RequestException
from pyspark import SparkContext

old_gen_filename=Artifact._generate_filename
def myGenFileName(self):
    if self.version:
        s = self.artifact_id + "-" + self.version
        if not self.classifier:
            return  s + "." + self.extension
        else:
            return s + "-" + self.classifier + "." + self.extension 
    else:
        return old_gen_filename(self)
            
Artifact._generate_filename=myGenFileName

class PackageManager(object):
    PACKAGES_TBL="SPARK_PACKAGES"
    DOWNLOAD_DIR=os.path.expanduser('~') + "/data/libs"
    def row_dict_factory(self,cursor,row):
        res={}
        for i,col in enumerate(cursor.description):
            res[col[0]]=row[i]
        return res
    
    def __init__(self):
        self.conn = sqlite3.connect('spark.db')
        self.conn.row_factory=self.row_dict_factory 
        print("Opened database successfully")
        if not os.path.exists(self.DOWNLOAD_DIR):
            os.makedirs(self.DOWNLOAD_DIR)
        self._initTable()
        
    def _initTable(self):
        cursor=self.conn.execute("""
            SELECT * FROM sqlite_master WHERE name ='{0}' and type='table';
        """.format(self.PACKAGES_TBL))
        if cursor.fetchone() is None:
            self.conn.execute('''CREATE TABLE {0} (
                   GROUPID        TEXT  NOT NULL,
                   ARTIFACTID     TEXT  NOT NULL,
                   VERSION        TEXT  NOT NULL,
                   FILEPATH       TEXT  NOT NULL,
                   BASE           TEXT,
                   PRIMARY KEY (GROUPID, ARTIFACTID)
                   );
            '''.format(self.PACKAGES_TBL))
            print("Table created successfully")
        cursor.close()
    
    def _toArtifact(self, artifact):
        if isinstance(artifact, basestring):
            artifact=Artifact.parse(artifact)
        return artifact
    
    def installPackage(self, artifact, base=None, sc=None):
        artifact = self._toArtifact(artifact)
        #Test if we already have a version installed
        res=self.fetchArtifact(artifact)
        fileLoc=None
        if res:
            fileLoc=res[1]
            print("Package already installed: {0}".format(str(artifact)))
        else:
            #download package
            art=[artifact]
            def _doDownload(d):
                artifact=art[0]
                if not artifact.version or artifact.version=='0':
                    artifact.version = d.resolver._find_latest_version_available(artifact)
                fileLoc = artifact.get_filename(self.DOWNLOAD_DIR)
                if os.path.isfile(fileLoc):
                    os.remove(fileLoc)
                results = d.download(artifact,filename=self.DOWNLOAD_DIR)
                if not results[1]:
                    raise Exception("Error downloading package {0}".format(str(artifact)))
                else:
                    artifact=results[0]
                    print("Artifact downloaded successfully {0}".format(str(artifact)))
                    printEx("Please restart Kernel to complete installation of the new package",PrintColors.RED)
                fileLoc=self.storeArtifact(artifact,base)
                return fileLoc
            
            try:
                fileLoc=_doDownload(downloader.Downloader(base) if base is not None else downloader.Downloader())
            except RequestException as e:
                #try another base
                try:
                    fileLoc=_doDownload(downloader.Downloader("http://dl.bintray.com/spark-packages/maven"))
                except RequestException as e:
                    print("Unable to install artifact {0}".format(e.msg))
                    raise
            except:
                print(str(sys.exc_info()[1]))
                raise
        if sc is None:
            sc = SparkContext.getOrCreate()
            
        if sc:
            #convert to file uri for windows platform
            if platform.system()=='Windows':
                fileLoc="file://" + urllib.pathname2url(fileLoc)
            sc.addPyFile(fileLoc)
            
        return artifact
        
    def uninstallPackage(self, artifact):
        results = self.fetchArtifact(artifact)
        if results is None:
            print("Package is not installed: {0}".format(str(artifact)))
        else:
            self._deleteArtifact(results[0],results[1])
    
    def hasArtifact(self, artifact):
        return self.fetchArtifact(artifact) is not None
        
    def fetchArtifact(self, artifact ):
        artifact = self._toArtifact(artifact)
        cursor=None
        try:
            cursor=self.conn.execute("""
                SELECT * from {0} WHERE GROUPID='{1}' and ARTIFACTID='{2}'
                """.format(self.PACKAGES_TBL,artifact.group_id,artifact.artifact_id)
            )
            row = cursor.fetchone()
            return (Artifact(row["GROUPID"],row["ARTIFACTID"],row["VERSION"]),row["FILEPATH"]) if row else None
        finally:
            if cursor is not None:
                cursor.close()
                
    def printAllPackages(self):
        self.visitAll(lambda row: print("{0}:{1}:{2} => {3}".format(row["GROUPID"],row["ARTIFACTID"],row["VERSION"],row["FILEPATH"])))
        
    def visitAll(self, walker):
        cursor=self.conn.execute("""
                SELECT * FROM {0}
            """.format(self.PACKAGES_TBL)
        )
        for row in cursor:
            walker(row)
        cursor.close()
        
    def storeArtifact(self, artifact,base=None):
        artifact = self._toArtifact(artifact)
        fileLoc=artifact.get_filename(self.DOWNLOAD_DIR)
        self.conn.execute("""
            INSERT INTO {0} (GROUPID,ARTIFACTID,VERSION,BASE,FILEPATH)
            VALUES ('{1}','{2}','{3}','{4}','{5}')
        """.format(
                self.PACKAGES_TBL,
                artifact.group_id,
                artifact.artifact_id,
                artifact.version,
                base if base is not None else "",
                fileLoc
            )
        )
        self.conn.commit()
        print("Successfully added artifact {0}".format(str(artifact)))
        return fileLoc
        
    def _deleteArtifact(self,artifact,filePath):
        artifact = self._toArtifact(artifact)
        cursor=self.conn.execute("""
            DELETE FROM {0} WHERE GROUPID='{1}' AND ARTIFACTID='{2}'
        """.format(
                self.PACKAGES_TBL,
                artifact.group_id,
                artifact.artifact_id
            )
        )
        self.conn.commit()
        if self.conn.total_changes==0:
            print("Artifact {0} not deleted because it doesn't exist")
        else:
            print("Successfully deleted artifact {0}".format(str(artifact)))
            
        if filePath is not None:
            os.remove(filePath)
    
    def __del__(self):
        self.conn.close()