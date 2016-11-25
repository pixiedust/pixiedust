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
# Inherited from maven-artifact https://github.com/hamnis/maven-artifact
# -------------------------------------------------------------------------------

import hashlib
import os
from .package import Package
from lxml import etree
import uuid
from IPython.display import display, HTML, Javascript

try:
    from urllib.request import Request, urlopen, URLError, HTTPError
except ImportError:
    from urllib2 import Request, urlopen, URLError, HTTPError

def doRequest(url, onFail, onSuccess, username=None, password=None):
        headers = {"User-Agent": "PixieDust PackageManager/1.0"}
        if username and password:
            import base64
            headers["Authorization"] = "Basic " + base64.b64encode(self.username + ":" + self.password)
        req = Request(url, None, headers)
        try:
            response = urlopen(req)
        except HTTPError as e:
            onFail(url, e)
        except URLError as e:
            onFail(url, e)
        else:
            return onSuccess(response)

class Resolver(object):
    def __init__(self, base):
        if base.endswith("/"):
            base = base.rstrip("/")
        self.base = base

    def _parseMetadataXML(self, r):
        try:
            return etree.parse(r)
        except e:
            print(e)

    def _find_latest_version_available(self, package):
        path = "/%s/maven-metadata.xml" % (package.path(False))
        xml = doRequest(self.base + path, self._onFail, lambda r: self._parseMetadataXML(r))
        v = xml.xpath("/metadata/versioning/versions/version[last()]/text()")
        if v:
            return v[0]

    def _onFail(self, url, e):
        raise RequestException("Failed to download maven-metadata.xml from '%s'" % url)

    def resolve(self, package):
        version = package.version
        if not package.version or package.version == "latest":            
            version = self._find_latest_version_available(package)
        return Package.clone(package)

    def uri_for_artifact(self, package):        
        resolved = self.resolve(package)
        return package.getUri(self.base, resolved.version)

class RequestException(Exception):
    def __init__(self, msg):
        self.msg = msg

class Downloader(object):
    def __init__(self, base="http://repo1.maven.org/maven2", username=None, password=None):
        self.username = username
        self.password = password
        self.resolver = Resolver(base)
        self.prefix = str(uuid.uuid4())[:8]
    
    def download(self, package, filename=None, suppress_log=False):
        filename = package.getFilePath(filename)
        url = self.resolver.uri_for_artifact(package)
        if not self.verify_md5(filename, url + ".md5"):
            if not suppress_log:
                hook=self._chunk_report
            else:
                hook=self._chunk_report_suppress

            onError = lambda uri, err: self._throwDownloadFailed("Failed to download package " + str(package) + "from " + uri)
            response = doRequest(url, onError, lambda r: r)
            
            if response:
                if not suppress_log:
                    print("Downloading package {0} to {1}".format(package, filename))
                with open(filename, 'wb') as f:
                    self._write_chunks(response, f, report_hook=hook)
                return (package, True)
            else:
                return (package, False)
        else:
            if not suppress_log:
                print("%s is already up to date" % package)
            return (package, True)

    def _throwDownloadFailed(self, msg):
        raise RequestException(msg)

    def _chunk_report_suppress(self, bytes_so_far, chunk_size, total_size):
        pass

    def _chunk_report(self, bytes_so_far, chunk_size, total_size):
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

    def _write_chunks(self, response, file, chunk_size=8192, report_hook=None):
        total_size = response.headers['Content-Length'].strip()
        total_size = int(total_size)
        bytes_so_far = 0

        if report_hook:
                report_hook(bytes_so_far, chunk_size, total_size)

        while 1:
            chunk = response.read(chunk_size)
            bytes_so_far += len(chunk)

            if not chunk:
                break

            file.write(chunk)
            if report_hook:
                report_hook(bytes_so_far, chunk_size, total_size)

        return bytes_so_far

    def verify_md5(self, file, remote_md5):
        if not os.path.exists(file):
            return False
        else:
            local_md5 = self._local_md5(file)
            onError = lambda uri, err: _throwDownloadFailed("Failed to download MD5 from " + uri)
            remote = doRequest(remote_md5, onError, lambda r: r.read())
            return local_md5 == remote

    def _local_md5(self, file):
        md5 = hashlib.md5()
        with open(file, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), ''):
                md5.update(chunk)
        return md5.hexdigest()
