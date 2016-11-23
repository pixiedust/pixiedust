from lxml import etree

from .requestor import RequestException
from .package import Package

class Resolver(object):
    def __init__(self, base, requestor):    
        self.requestor = requestor
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
        xml = self.requestor.request(self.base + path, self._onFail, lambda r: self._parseMetadataXML(r))
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
