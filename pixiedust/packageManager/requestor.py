import base64
try:
    from urllib.request import Request, urlopen, URLError, HTTPError
except ImportError:
    from urllib2 import Request, urlopen, URLError, HTTPError

class Requestor(object):
    def __init__(self, username = None, password = None, user_agent = "Maven Artifact Downloader/1.0"):    
        self.user_agent = user_agent
        self.username = username
        self.password = password


    def request(self, url, onFail, onSuccess):
        headers = {"User-Agent": self.user_agent}
        if self.username and self.password:
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

class RequestException(Exception):
    def __init__(self, msg):
        self.msg = msg
