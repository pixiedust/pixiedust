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

from __future__ import print_function
import sqlite3
import sys
import platform
import urllib
import os
from pixiedust.utils.storage import *
from pixiedust.utils.printEx import *
from pyspark import SparkContext
from .package import Package
from .downloader import Downloader, RequestException
import six

PACKAGES_TBL_NAME="SPARK_PACKAGES"

class __PackageStorage(Storage):
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

packageStorage = __PackageStorage()

class PackageManager(object):
    DOWNLOAD_DIR=os.environ.get("PIXIEDUST_HOME", os.path.expanduser('~')) + "/data/libs"
    
    def __init__(self):
        if not os.path.exists(self.DOWNLOAD_DIR):
            os.makedirs(self.DOWNLOAD_DIR)

    def _toPackage(self, package):
        if isinstance(package, six.string_types):
            package=Package.fromPackageIdentifier(package)
        return package
    
    def installPackage(self, package, base=None, sc=None):
        package = self._toPackage(package)
        #Test if we already have a version installed
        res=self.fetchPackage(package)
        fileLoc=None
        if res:
            fileLoc=res[1]
            print("Package already installed: {0}".format(str(package)))
        else:
            #download package
            packs=[package]
            def _doDownload(d):
                package=packs[0]
                if not package.version or package.version=='0':
                    package.version = d.resolver._find_latest_version_available(package)
                fileLoc = package.getFilePath(self.DOWNLOAD_DIR)
                if os.path.isfile(fileLoc):
                    os.remove(fileLoc)
                results = d.download(package,filename=self.DOWNLOAD_DIR)
                if not results[1]:
                    raise Exception("Error downloading package {0}".format(str(package)))
                else:
                    package=results[0]
                    print("Package {0} downloaded successfully".format(str(package)))
                    printEx("Please restart Kernel to complete installation of the new package",PrintColors.RED)
                fileLoc=self.storePackage(package,base)
                return fileLoc
            
            try:
                fileLoc=_doDownload(Downloader(base) if base is not None else Downloader())
            except RequestException as e:
                #try another base
                try:
                    fileLoc=_doDownload(Downloader("http://dl.bintray.com/spark-packages/maven"))
                except RequestException as e:
                    print("Unable to install package {0}".format(e.msg))
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
            
        return package
        
    def uninstallPackage(self, package):
        results = self.fetchPackage(package)
        if results is None:
            print("Package is not installed: {0}".format(str(package)))
        else:
            self._deletePackage(results[0],results[1])
    
    def hasPackage(self, package):
        return self.fetchPackage(package) is not None
        
    def fetchPackage(self, package ):
        package = self._toPackage(package)
        return packageStorage.fetchOne("""
                SELECT * from {0} WHERE GROUPID='{1}' and ARTIFACTID='{2}'
            """.format(PACKAGES_TBL_NAME,package.group_id,package.artifact_id), 
            lambda row: (Package(row["GROUPID"],row["ARTIFACTID"],row["VERSION"]),row["FILEPATH"])
        )
                
    def printAllPackages(self):
        self.visitAll(lambda row: print("{0}:{1}:{2} => {3}".format(row["GROUPID"],row["ARTIFACTID"],row["VERSION"],row["FILEPATH"])))
        
    def visitAll(self, walker):
        packageStorage.execute("""
                SELECT * FROM {0}
            """.format(PACKAGES_TBL_NAME),
            walker
        )
        
    def storePackage(self, package,base=None):
        package = self._toPackage(package)
        fileLoc=package.getFilePath(self.DOWNLOAD_DIR)
        packageStorage.insert("""
            INSERT INTO {0} (GROUPID,ARTIFACTID,VERSION,BASE,FILEPATH)
            VALUES ('{1}','{2}','{3}','{4}','{5}')
        """.format(
                PACKAGES_TBL_NAME,
                package.group_id,
                package.artifact_id,
                package.version,
                base if base is not None else "",
                fileLoc
            )
        )
        print("Successfully added package {0}".format(str(package)))
        return fileLoc
        
    def _deletePackage(self,package,filePath):
        package = self._toPackage(package)
        rowDeleted = packageStorage.delete("""
            DELETE FROM {0} WHERE GROUPID='{1}' AND ARTIFACTID='{2}'
        """.format(
                PACKAGES_TBL_NAME,
                package.group_id,
                package.artifact_id
            )
        )
        if rowDeleted==0:
            print("Package {0} not deleted because it doesn't exist".format(str(package)))
        else:
            print("Successfully deleted package {0}".format(str(package)))
            
        if filePath is not None:
            os.remove(filePath)
    