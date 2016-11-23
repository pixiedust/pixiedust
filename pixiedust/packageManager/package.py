import os

class Package(object):
    def __init__(self, group_id, artifact_id, version):
        if not group_id:
            raise ValueError("group_id must be set")
        if not artifact_id:
            raise ValueError("artifact_id must be set")

        self.group_id = group_id
        self.artifact_id = artifact_id
        self.version = version
        self.uri = None

    def path(self, with_version=True):
        base = self.group_id.replace(".", "/") + "/" + self.artifact_id
        if with_version:
            return base + "/" + self.version
        else:
            return base

    def getUri(self, base, resolved_version=None):
        if self.uri:
            return self.uri
        if not resolved_version:
            resolved_version = self.version
        return base + "/" + self.path() + "/" + self.artifact_id + "-" + resolved_version + ".jar"

    def _generateFileName(self):
        s = self.artifact_id
        if self.version:
            s = s + "-" + self.version
        return s + ".jar"

    def getFilePath(self, filename=None):
        if  self.uri:
            return os.path.join(dir, uri.split("/")[-1])

        if not filename:
            filename = self._generateFileName()
        elif os.path.isdir(filename):
            filename = os.path.join(filename, self._generateFileName())
        return filename

    @staticmethod
    def clone(package, version=None):
        return Package(
            package.group_id,
            package.artifact_id,
            version if version is not None else package.version)

    @staticmethod
    def fromPackageIdentifier(package):
        #check if the user wants a direct download
        if package.startswith("http://") or package.startswith("https://") or package.startswith("file://"):
            retPackage = Package( "direct.download", package, "1.0" )
            retPackage.uri = package
            return retPackage

        parts = package.split(":")
        if len(parts) >= 3:
            g = parts[0]
            a = parts[1]
            v = parts[len(parts) - 1]
            return Package(g, a, v)
        return None
