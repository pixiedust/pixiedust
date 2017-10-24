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
import pixiedust
from pixiedust.utils.shellAccess import ShellAccess
from pixiedust.utils.template import PixiedustTemplateEnvironment
from pixiedust.utils.environment import Environment,scalaGateway
import pandas as pd
import uuid
import tempfile
from collections import OrderedDict
from IPython.display import display, HTML, Javascript
import json
import requests
from pandas.io.json import json_normalize
try:
    from urllib.request import Request, urlopen, URLError, HTTPError
except ImportError:
    from urllib2 import Request, urlopen, URLError, HTTPError

dataDefs = OrderedDict([
    ("1", {
        "displayName": "Car performance data",
        "url": "https://github.com/ibm-watson-data-lab/open-data/raw/master/cars/cars.csv",
        "topic": "Transportation",
        "publisher": "IBM",
        "schema2": [('mpg','int'),('cylinders','int'),('engine','double'),('horsepower','int'),('weight','int'),
            ('acceleration','double'),('year','int'),('origin','string'),('name','string')]
    }),
    ("2", {
        "displayName": "Sample retail sales transactions, January 2009",
        "url": "https://raw.githubusercontent.com/ibm-watson-data-lab/open-data/master/salesjan2009/salesjan2009.csv",
        "topic": "Economy & Business",
        "publisher": "IBM Cloud Data Services"
    }),
    ("3", {
        "displayName": "Total population by country",
        "url": "https://apsportal.ibm.com/exchange-api/v1/entries/889ca053a19986a4445839358a91963e/data?accessKey=657b130d504ab539947e51b50f0e338e",
        "topic": "Society",
        "publisher": "IBM Cloud Data Services"
    }),
    ("4", {
        "displayName": "GoSales Transactions for Naive Bayes Model",
        "url": "https://apsportal.ibm.com/exchange-api/v1/entries/8044492073eb964f46597b4be06ff5ea/data?accessKey=bec2ed69d9c84bed53826348cdc5690b",
        "topic": "Leisure",
        "publisher": "IBM"
    }),
    ("5", {
        "displayName": "Election results by County",
        "url": "https://openobjectstore.mybluemix.net/Election/county_election_results.csv",
        "topic": "Society",
        "publisher": "IBM"
    }),
    ("6", {
        "displayName": "Million dollar home sales in NE Mass late 2016",
        "url": "https://openobjectstore.mybluemix.net/misc/milliondollarhomes.csv",
        "topic": "Economy & Business",
        "publisher": "Redfin.com"
    }),
    ("7", {
        "displayName": "Boston Crime data, 2-week sample",
        "url": "https://raw.githubusercontent.com/ibm-watson-data-lab/open-data/master/crime/boston_crime_sample.csv",
        "topic": "Society",
        "publisher": "City of Boston"
    })
])

@scalaGateway
def sampleData(dataId=None, type='csv', forcePandas=False):
    global dataDefs
    return SampleData(dataDefs, forcePandas).sampleData(dataId, type)

class SampleData(object):
    env = PixiedustTemplateEnvironment()
    def __init__(self, dataDefs, forcePandas):
        self.dataDefs = dataDefs
        self.forcePandas = forcePandas
        self.url = ""

    def sampleData(self, dataId = None, type='csv'):
        if dataId is None:
            self.printSampleDataList()
        elif str(dataId) in dataDefs:
            return self.loadSparkDataFrameFromSampleData(dataDefs[str(dataId)])
        elif "https://" in str(dataId) or "http://" in str(dataId) or "file://" in str(dataId):
            if type is 'json':
                self.url = str(dataId)
                return self.JSONloadSparkDataFrameFromUrl(str(dataId))
            else:
                return self.loadSparkDataFrameFromUrl(str(dataId))
        else:
            print("Unknown sample data identifier. Please choose an id from the list below")
            self.printSampleDataList()

    def printSampleDataList(self):
        display( HTML( self.env.getTemplate("sampleData.html").render( dataDefs = iteritems(self.dataDefs) ) ))

    def dataLoader(self, path, schema=None):
        if schema is not None and Environment.hasSpark:
            from pyspark.sql.types import StructType,StructField,IntegerType,DoubleType,StringType
            def getType(t):
                if t == 'int':
                    return IntegerType()
                elif t == 'double':
                    return DoubleType()
                else:
                    return StringType()

        if Environment.hasSpark and not self.forcePandas:
            if Environment.sparkVersion == 1:
                print("Loading file using 'com.databricks.spark.csv'")
                load = ShellAccess.sqlContext.read.format('com.databricks.spark.csv')
                if schema is not None:
                    return load.options(header='true', mode="DROPMALFORMED").load(path, schema=StructType([StructField(item[0], getType(item[1]), True) for item in schema]))
                else:
                    return load.options(header='true', mode="DROPMALFORMED", inferschema='true').load(path)
            else:
                print("Loading file using 'SparkSession'")
                csvload = ShellAccess.SparkSession.builder.getOrCreate() \
                    .read \
                    .format("org.apache.spark.sql.execution.datasources.csv.CSVFileFormat") \
                    .option("header", "true") \
                    .option("mode", "DROPMALFORMED")
                if schema is not None:
                    return csvload.schema(StructType([StructField(item[0], getType(item[1]), True) for item in schema])).load(path)
                else:
                    return csvload.option("inferSchema", "true").load(path)
        else:
            print("Loading file using 'pandas'")
            return pd.read_csv(path)

    def JSONdataLoader(self, path, schema=None):
        if schema is not None and Environment.hasSpark:
            from pyspark.sql.types import StructType,StructField,IntegerType,DoubleType,StringType
            def getType(t):
                if t == 'int':
                    return IntegerType()
                elif t == 'double':
                    return DoubleType()
                else:
                    return StringType()

        res = open(path, 'r').read()
        if Environment.hasSpark and not self.forcePandas:
            if Environment.sparkVersion == 1:
                print("Loading file using a pySpark DataFrame for Spark 1")
                dataRDD = ShellAccess.sc.parallelize([res])
                return ShellAccess.sqlContext.jsonRDD(dataRDD)
            else:
                print("Loading file using a pySpark DataFrame for Spark 2")
                dataRDD = ShellAccess.sc.parallelize([res])
                return ShellAccess.spark.read.json(dataRDD)
        else:
            print("Loading file using 'pandas'")
            data = json.loads(res)
            df = json_normalize(data)
            return df

    def loadSparkDataFrameFromSampleData(self, dataDef):
        return Downloader(dataDef, self.forcePandas).download(self.dataLoader)

    def loadSparkDataFrameFromUrl(self, dataUrl):
        i = dataUrl.rfind('/')
        dataName = dataUrl[(i+1):]
        dataDef = {
            "displayName": dataUrl,
            "url": dataUrl
        }

        return Downloader(dataDef, self.forcePandas).download(self.dataLoader)

    def JSONloadSparkDataFrameFromUrl(self, dataUrl):
        i = dataUrl.rfind('/')
        dataName = dataUrl[(i+1):]
        dataDef = {
            "displayName": dataUrl,
            "url": dataUrl
        }

        return Downloader(dataDef, self.forcePandas).download(self.JSONdataLoader)

# Use of progress Monitor doesn't render correctly when previewed a saved notebook, turning it off until solution is found
useProgressMonitor = False
class Downloader(object):
    def __init__(self, dataDef, forcePandas):
        self.dataDef = dataDef
        self.forcePandas = forcePandas
        self.headers = {"User-Agent": "PixieDust Sample Data Downloader/1.0"}
        self.prefix = str(uuid.uuid4())[:8]

    def download(self, dataLoader):
        displayName = self.dataDef["displayName"]
        bytesDownloaded = 0
        if "path" in self.dataDef:
            path = self.dataDef["path"]
        else:
            url = self.dataDef["url"]
            req = Request(url, None, self.headers)
            print("Downloading '{0}' from {1}".format(displayName, url))
            with tempfile.NamedTemporaryFile(delete=False) as f:
                bytesDownloaded = self.write(urlopen(req), f)
                path = f.name            
            if url.endswith(".zip"):
                #unzip first and get the first file in it
                print("Extracting first item in zip file...")
                import zipfile
                import shutil
                zfile = zipfile.ZipFile(path, 'r')
                if len(zfile.filelist)==0:
                    raise(Exception("Error: zip file is empty"))
                with tempfile.NamedTemporaryFile(delete=False) as zf:
                    with zfile.open( zfile.filelist[0], 'r') as first_file:
                        print("File extracted: {}".format(first_file.name))
                        shutil.copyfileobj( first_file, zf)
                    path = zf.name
                
            self.dataDef["path"] = path
            self.dataDef["transient"] = True
            global dataDefs
            dataDefs[url] = self.dataDef
        if path:
            try:
                if bytesDownloaded > 0:
                   print("Downloaded {} bytes".format(bytesDownloaded))
                print("Creating {1} DataFrame for '{0}'. Please wait...".\
                    format(displayName, 'pySpark' if Environment.hasSpark and not self.forcePandas else 'pandas'))
                return dataLoader(path, self.dataDef.get("schema", None))
            finally:
                print("Successfully created {1} DataFrame for '{0}'".\
                    format(displayName, 'pySpark' if Environment.hasSpark and not self.forcePandas else 'pandas'))

    def report(self, bytes_so_far, chunk_size, total_size):
        if useProgressMonitor:
            if bytes_so_far == 0:
                display( HTML( """
                    <div>
                        <span id="pm_label{0}">Starting download...</span>
                        <progress id="pm_progress{0}" max="100" value="0" style="width:200px"></progress>
                    </div>""".format(self.prefix)
                    )
                )
            else:
                percent = float(bytes_so_far) / total_size
                percent = round(percent*100, 2)
                display(
                    Javascript("""
                        $("#pm_label{prefix}").text("{label}");
                        $("#pm_progress{prefix}").attr("value", {percent});
                    """.format(prefix=self.prefix, label="Downloaded {0} of {1} bytes".format(bytes_so_far, total_size), percent=percent))
                )

    def write(self, response, file, chunk_size=8192):
        total_size = response.headers['Content-Length'].strip() if 'Content-Length' in response.headers else 100
        total_size = int(total_size)
        bytes_so_far = 0

        self.report(bytes_so_far, chunk_size, total_size)

        while 1:
            chunk = response.read(chunk_size)
            bytes_so_far += len(chunk)
            if not chunk:
                break
            file.write(chunk)
            total_size = bytes_so_far if bytes_so_far > total_size else total_size
            self.report(bytes_so_far, chunk_size, total_size)

        return bytes_so_far
