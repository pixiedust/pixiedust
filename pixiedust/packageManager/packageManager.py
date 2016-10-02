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
from pixiedust.utils.storage import *
from pixiedust.utils.printEx import *
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

PACKAGES_TBL_NAME="SPARK_PACKAGES"

class __ArtifactStorage(Storage):
    def __init__(self):
        self._initTable( PACKAGES_TBL_NAME,
        '''
            GROUPID        TEXT  NOT NULL,
            ARTIFACTID     TEXT  NOT NULL,
            VERSION        TEXT  NOT NULL,
            FILEPATH       TEXT  NOT NULL,
            BASE           TEXT,
            PRIMARY KEY (GROUPID, ARTIFACTID)
        ''')

artifactStorage = __ArtifactStorage()

class PackageManager(object):
    DOWNLOAD_DIR=os.path.expanduser('~') + "/data/libs"
    
    def __init__(self):
        if not os.path.exists(self.DOWNLOAD_DIR):
            os.makedirs(self.DOWNLOAD_DIR)

    def _toArtifact(self, artifact):
        if isinstance(artifact, basestring):
            #check if the user wants a direct download
            if artifact.startswith("http://") or artifact.startswith("https://") or artifact.startswith("file://"):
                url=artifact
                artifact=type("",(),
                    {
                        "group_id":"direct.download",
                        "artifact_id": artifact,
                        "version":"1.0",
                        "get_filename":lambda self,dir: os.path.join(dir, url.split("/")[-1] ),
                        "is_snapshot": lambda self:False,
                        "with_version": lambda self,version:self,
                        "uri": lambda self, base, version: url,
                        "__str__": lambda self: url
                    }
                )()
            else:
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
        return artifactStorage.fetchOne("""
                SELECT * from {0} WHERE GROUPID='{1}' and ARTIFACTID='{2}'
            """.format(PACKAGES_TBL_NAME,artifact.group_id,artifact.artifact_id), 
            lambda row: (Artifact(row["GROUPID"],row["ARTIFACTID"],row["VERSION"]),row["FILEPATH"])
        )
                
    def printAllPackages(self):
        self.visitAll(lambda row: print("{0}:{1}:{2} => {3}".format(row["GROUPID"],row["ARTIFACTID"],row["VERSION"],row["FILEPATH"])))
        
    def visitAll(self, walker):
        artifactStorage.execute("""
                SELECT * FROM {0}
            """.format(PACKAGES_TBL_NAME),
            walker
        )
        
    def storeArtifact(self, artifact,base=None):
        artifact = self._toArtifact(artifact)
        fileLoc=artifact.get_filename(self.DOWNLOAD_DIR)
        artifactStorage.insert("""
            INSERT INTO {0} (GROUPID,ARTIFACTID,VERSION,BASE,FILEPATH)
            VALUES ('{1}','{2}','{3}','{4}','{5}')
        """.format(
                PACKAGES_TBL_NAME,
                artifact.group_id,
                artifact.artifact_id,
                artifact.version,
                base if base is not None else "",
                fileLoc
            )
        )
        print("Successfully added artifact {0}".format(str(artifact)))
        return fileLoc
        
    def _deleteArtifact(self,artifact,filePath):
        artifact = self._toArtifact(artifact)
        rowDeleted = artifactStorage.delete("""
            DELETE FROM {0} WHERE GROUPID='{1}' AND ARTIFACTID='{2}'
        """.format(
                PACKAGES_TBL_NAME,
                artifact.group_id,
                artifact.artifact_id
            )
        )
        if rowDeleted==0:
            print("Artifact {0} not deleted because it doesn't exist".format(str(artifact)))
        else:
            print("Successfully deleted artifact {0}".format(str(artifact)))
            
        if filePath is not None:
            os.remove(filePath)
    