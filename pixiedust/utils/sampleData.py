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
from six import iteritems
from pyspark.sql.types import *
import pixiedust
from pixiedust.utils.shellAccess import ShellAccess
from pixiedust.utils.template import PixiedustTemplateEnvironment
from pixiedust.utils.environment import Environment,scalaGateway
import uuid
import tempfile
from collections import OrderedDict
from IPython.display import display, HTML, Javascript
try:
    from urllib.request import Request, urlopen, URLError, HTTPError
except ImportError:
    from urllib2 import Request, urlopen, URLError, HTTPError

dataDefs = OrderedDict([
    ("1", {
        "displayName": "Car performance data", 
        "url": "https://github.com/ibm-cds-labs/open-data/raw/master/cars/cars.csv",
        "topic": "transportation",
        "publisher": "IBM",
        "schema2": [('mpg','int'),('cylinders','int'),('engine','double'),('horsepower','int'),('weight','int'),
            ('acceleration','double'),('year','int'),('origin','string'),('name','string')]
    }),
    ("2", {
        "displayName": "Sample retail sales transactions, January 2009", 
        "url": "https://raw.githubusercontent.com/ibm-cds-labs/open-data/master/salesjan2009/salesjan2009.csv",
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
        "url": "https://raw.githubusercontent.com/ibm-cds-labs/open-data/master/crime/boston_crime_sample.csv",
        "topic": "Society",
        "publisher": "City of Boston"
    })
])

@scalaGateway
def sampleData(dataId=None):
    global dataDefs
    return SampleData(dataDefs).sampleData(dataId)

class SampleData(object):
    env = PixiedustTemplateEnvironment()
    def __init__(self, dataDefs):
        self.dataDefs = dataDefs

    def sampleData(self, dataId = None):
        if dataId is None:
            self.printSampleDataList()
        elif str(dataId) in dataDefs:
            return self.loadSparkDataFrameFromSampleData(dataDefs[str(dataId)])
        elif "https://" in str(dataId) or "http://" in str(dataId):
            return self.loadSparkDataFrameFromUrl(str(dataId))
        else:
            print("Unknown sample data identifier. Please choose an id from the list below")
            self.printSampleDataList()

    def printSampleDataList(self):
        display( HTML( self.env.getTemplate("sampleData.html").render( dataDefs = iteritems(self.dataDefs) ) ))
        #for key, val in iteritems(self.dataDefs):
        #    print("{0}: {1}".format(key, val["displayName"]))

    def dataLoader(self, path, schema=None):
        #TODO: if in Spark 2.0 or higher, use new API to load CSV
        load = ShellAccess["sqlContext"].read.format('com.databricks.spark.csv')
        if schema is not None:
            def getType(t):
                if t == 'int':
                    return IntegerType()
                elif t == 'double':
                    return DoubleType()
                else:
                    return StringType()
            return load.options(header='true', mode="DROPMALFORMED").load(path, schema=StructType([StructField(item[0], getType(item[1]), True) for item in schema]))
        else:
            return load.options(header='true', mode="DROPMALFORMED", inferschema='true').load(path)

    def loadSparkDataFrameFromSampleData(self, dataDef):
        return Downloader(dataDef).download(self.dataLoader)

    def loadSparkDataFrameFromUrl(self, dataUrl):
        i = dataUrl.rfind('/')
        dataName = dataUrl[(i+1):]
        dataDef = {
            "displayName": dataUrl,
            "url": dataUrl
        }
        return Downloader(dataDef).download(self.dataLoader)


class Downloader(object):
    def __init__(self, dataDef):
        self.dataDef = dataDef
        self.headers = {"User-Agent": "PixieDust Sample Data Downloader/1.0"}
        self.prefix = str(uuid.uuid4())[:8]
    
    def download(self, dataLoader):
        displayName = self.dataDef["displayName"]
        if "path" in self.dataDef:
            path = self.dataDef["path"]
        else:
            url = self.dataDef["url"]
            req = Request(url, None, self.headers)
            print("Downloading '{0}' from {1}".format(displayName, url))
            with tempfile.NamedTemporaryFile(delete=False) as f:
                self.write(urlopen(req), f)
                path = f.name
                self.dataDef["path"] = path = f.name
        if path:
            try:
                print("Creating pySpark DataFrame for '{0}'. Please wait...".format(displayName))
                return dataLoader(path, self.dataDef.get("schema", None))
            finally:
                print("Successfully created pySpark DataFrame for '{0}'".format(displayName))
            
    def report(self, bytes_so_far, chunk_size, total_size):
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