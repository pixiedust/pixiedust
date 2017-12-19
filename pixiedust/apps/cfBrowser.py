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

from pixiedust.display.app import *
from pixiedust.utils.userPreferences import *
import base64
import requests

access_token_key = 'cf.access_token'
api_base_url = 'api.ng.bluemix.net'
login_base_url = 'login.ng.bluemix.net'
    
@PixieApp
class CFBrowser:


    def get_data_frame(self):
        return self.df
    
    @route(login="true")
    def _login(self):
        # Login
        body = 'grant_type=password&passcode={}'.format(self.passcode)
        url = 'https://{}/UAALoginServerWAR/oauth/token'.format(login_base_url)
        r = requests.post(url, data=body, headers={
            'Authorization': 'Basic Y2Y6',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        })
        json = r.json()
        if 'access_token' in json.keys():
            self.access_token = json['access_token']
            setUserPreference(access_token_key, self.access_token)
        self.show_orgs()
        
    def show_orgs(self):
        # Load organizations
        orgs = self.get_orgs(self.access_token)
        options = ""
        for org in orgs:
            options += """<option value="{}">{}</option>""".format(org['metadata']['guid'],org['entity']['name'])
        self._addHTMLTemplateString("""
<div>
  <div class="form-horizontal">
    <div class="form-group">
      <label for="org{{prefix}}" class="control-label col-sm-2">Select an organization:</label>
      <div class="col-sm-5">
        <select class="form-control" id="org{{prefix}}">""" + options + """</select>
      </div>
      <div class="col-sm-1">
        <button type="submit" class="btn btn-primary" pd_refresh>Go
          <pd_script>
self.org_id="$val(org{{prefix}})"
self.login="false"
self.select_org="true"
          </pd_script>
        </button>
      </div>
    </div>
  </div>
</div>
""")
        
    @route(select_org="true")
    def _select_org(self):
        spaces = self.get_spaces(self.access_token, self.org_id)
        options = ""
        for space in spaces:
            options += """<option value="{}">{}</option>""".format(space['metadata']['guid'],space['entity']['name'])
        self._addHTMLTemplateString("""
<div>
  <div class="form-horizontal">
    <div class="form-group">
      <label for="org{{prefix}}" class="control-label col-sm-2">Select a space:</label>
      <div class="col-sm-5">
        <select class="form-control" id="space{{prefix}}">""" + options + """</select>
      </div>
      <div class="col-sm-1">
        <button type="submit" class="btn btn-primary" pd_refresh>Go
          <pd_script>
self.space_id="$val(space{{prefix}})"
self.select_org="false"
self.select_space="true"
          </pd_script>
        </button>
      </div>
    </div>
  </div>
</div>
""")

    @route(select_space="true")
    def _select_space(self):
        svcs = self.get_services(self.access_token, self.space_id)
        output = """
<div>
    <div class="form-horizontal">
"""
        for svc in svcs:
            svc_label = self.get_service_label(self.access_token, svc['entity']['service_plan_guid'])
            svc_name = svc['entity']['name']
            if svc_label == 'cloudantNoSQLDB' or "cloudant" in svc_name.lower():
                svc_keys = self.get_service_keys(self.access_token, svc['metadata']['guid'])
                for svc_key in svc_keys:
                    svc_key_entity = svc_key['entity']
                    if 'credentials' in svc_key_entity.keys():
                        credentials_str = json.dumps(svc_key_entity['credentials'])
                        credentials_str = credentials_str.replace('"', '\\"')
                        output += """
<div class="form-group">
    <div class="col-sm-2"></div>
    <div class="col-sm-5">
        <b>""" + svc['entity']['name'] + """</b><br>
        """ + svc_key_entity['credentials']['host'] + """<br>
        <button type="submit" class="btn btn-primary" data-dismiss="modal" pd_refresh>Select
            <pd_script>self.service_name=\"""" + svc['entity']['name'].replace('"', '\\"') + """\"
self.credentials=\"""" + credentials_str + """\"
self.select_space="false"
self.select_credentials="true"</pd_script>
        </button>
    </div>
</div>"""
        return output

    @route(select_credentials="true")
    def _select_credentials(self):
        return self.selectBluemixCredentials(self.service_name, self.credentials)

    def is_valid_access_token(self, access_token):
        url = 'https://{}/v2/organizations'.format(api_base_url)
        authHeader = 'Bearer {}'.format(access_token)
        r = requests.get(url, headers={
            'Authorization': authHeader,
            'Accept': 'application/json'
        })
        return r.status_code == 200
        
    def get_orgs(self, access_token):
        url = 'https://{}/v2/organizations'.format(api_base_url)
        authHeader = 'Bearer {}'.format(access_token)
        r = requests.get(url, headers={
            'Authorization': authHeader,
            'Accept': 'application/json'
        })
        json = r.json()
        return json['resources']
        
    def get_spaces(self, access_token, org_id):
        url = 'https://{}/v2/organizations/{}/spaces'.format(api_base_url, org_id)
        authHeader = 'Bearer {}'.format(access_token)
        r = requests.get(url, headers={
            'Authorization': authHeader,
            'Accept': 'application/json'
        })
        json = r.json()
        return json['resources']
        
    def get_apps(self, access_token, space_id):
        url = 'https://{}/v2/apps?q=space_guid:{}'.format(api_base_url, space_id)
        authHeader = 'Bearer {}'.format(access_token)
        r = requests.get(url, headers={
            'Authorization': authHeader,
            'Accept': 'application/json'
        })
        json = r.json()
        return json['resources']
        
    def get_services(self, access_token, space_id):
        url = 'https://{}/v2/service_instances?q=space_guid:{}'.format(api_base_url, space_id)
        authHeader = 'Bearer {}'.format(access_token)
        r = requests.get(url, headers={
            'Authorization': authHeader,
            'Accept': 'application/json'
        })
        json = r.json()
        return json['resources']
    
    def get_service_keys(self, access_token, service_id):
        url = 'https://{}/v2/service_keys?q=service_instance_guid:{}'.format(api_base_url, service_id)
        authHeader = 'Bearer {}'.format(access_token)
        r = requests.get(url, headers={
            'Authorization': authHeader,
            'Accept': 'application/json'
        })
        json = r.json()
        return json['resources']
    
    def get_service_label(self, access_token, service_plan_id):
        # Load the service plan
        url = 'https://{}/v2/service_plans/{}'.format(api_base_url, service_plan_id)
        authHeader = 'Bearer {}'.format(access_token)
        r = requests.get(url, headers={
            'Authorization': authHeader,
            'Accept': 'application/json'
        })
        json = r.json()
        if 'entity' in json.keys():
            service_id = json['entity']['service_guid']
        else:
            return "NO PLAN FOUND"
        # Load the service
        url = 'https://{}/v2/services/{}'.format(api_base_url, service_id)
        path = '/v2/services/{}'.format(service_id)
        r = requests.get(url, headers={
            'Authorization': authHeader,
            'Accept': 'application/json'
        })
        json = r.json()
        return json['entity']['label']
        
    def cloudant_all_dbs(self, host, username, password):
        url = 'https://{}/_all_dbs'.format(host)
        r = requests.get(url, headers={
            'Authorization': 'Basic {}'.format(base64.b64encode('{}:{}'.format(username, password))),
            'Accept': 'application/json'
        })
        return r.json()

    @route()
    def startBrowsingBM(self):
        access_token_valid = False
        access_token = getUserPreference(access_token_key)
        if access_token is not None:
            access_token_valid = self.is_valid_access_token(access_token)
        if access_token_valid:
            self.access_token = access_token
            self.show_orgs()
        else:
            return """
<div>
  <div class="form-horizontal">
    <div class="form-group">
        <div class="col-sm-2"></div>
        <div class="col-sm-5">
            <a href="https://login.ng.bluemix.net/UAALoginServerWAR/passcode" target="_blank">
            Click here to get your one-time passcode
            </a>
        </div>
    </div>
    <div class="form-group">
      <label for="passcode{{prefix}}" class="control-label col-sm-2">Passcode:</label>
      <div class="col-sm-5">
        <input type="text" class="form-control" id="passcode{{prefix}}">
      </div>
      <div class="col-sm-1">
        <button type="submit" class="btn btn-primary" pd_refresh>Go
          <pd_script>
self.passcode="$val(passcode{{prefix}})"
self.login="true"
          </pd_script>
        </button>
      </div>
    </div>
  </div>
</div>
"""