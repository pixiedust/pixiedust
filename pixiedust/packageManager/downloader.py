import hashlib
import os
from .requestor import Requestor,RequestException
from .resolver import Resolver
import sys
import getopt

class Downloader(object):
    def __init__(self, base="http://repo1.maven.org/maven2", username=None, password=None):
        self.requestor = Requestor(username, password)
        self.resolver = Resolver(base, self.requestor)
    
    def download(self, package, filename=None, suppress_log=False):
        filename = package.getFilePath(filename)
        url = self.resolver.uri_for_artifact(package)
        if not self.verify_md5(filename, url + ".md5"):
            if not suppress_log:
                print("Downloading artifact " + str(package))
                hook=self._chunk_report
            else:
                hook=self._chunk_report_suppress

            onError = lambda uri, err: self._throwDownloadFailed("Failed to download artifact " + str(package) + "from " + uri)
            response = self.requestor.request(url, onError, lambda r: r)
            
            if response:
                with open(filename, 'wb') as f:
                    self._write_chunks(response, f, report_hook=hook)
                if not suppress_log:
                    print("Downloaded package %s to %s" % (package, filename))
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
        percent = float(bytes_so_far) / total_size
        percent = round(percent*100, 2)
        print("Downloaded %d of %d bytes (%0.2f%%)\r" % (bytes_so_far, total_size, percent))
        if bytes_so_far >= total_size:
            print()

    def _write_chunks(self, response, file, chunk_size=8192, report_hook=None):
        total_size = response.headers['Content-Length'].strip()
        total_size = int(total_size)
        bytes_so_far = 0

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
            remote = self.requestor.request(remote_md5, onError, lambda r: r.read())
            return local_md5 == remote

    def _local_md5(self, file):
        md5 = hashlib.md5()
        with open(file, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), ''):
                md5.update(chunk)
        return md5.hexdigest()
