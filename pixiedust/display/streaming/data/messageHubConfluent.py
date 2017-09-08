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

from pixiedust.display.streaming import *
from six import string_types, iteritems
import json
import os
try:
    from confluent_kafka import Consumer
except:
    from confluent_kafka_prebuilt import Consumer

class MessagehubStreamingAdapterConfluent(StreamingDataAdapter):
    def __init__(self, topic, username, password, prod=True):
        caLocation = '/etc/ssl/cert.pem'
        if not os.path.exists(caLocation):
            caLocation = '/etc/pki/tls/cert.pem'
        conf = {
            'client.id': 'pixieapp.client.id',
            'group.id': 'pixieapp.group',
            'security.protocol': 'SASL_SSL',
            'sasl.mechanisms': 'PLAIN',
            'ssl.ca.location': caLocation,
            "bootstrap.servers": ','.join(["kafka0{}-{}.messagehub.services.us-south.bluemix.net:9093".format(i, "prod01" if prod else "stage1") for i in range(1,6)]),
            "sasl.username": username,
            "sasl.password": password,
            'api.version.request': True
        }
        self.consumer = Consumer(conf)
        self.consumer.subscribe([topic])
        self.schema = {}
        self.sampleDocCount = 0
        
    def close(self):
        self.consumer.unsubscribe()
        self.consumer.close() 
        
    def tryCast(self, value, t):
        try:
            return t(value)
        except:
            return None
        
    def inferType(self, value):
        if isinstance(value, string_types):
            value = self.tryCast(value, int) or self.tryCast(value, long) or self.tryCast(value, float) or value
        return "integer" if value.__class__==int else "float" if value.__class__ == float else "string"
        
    def inferSchema(self, eventJSON):
        if self.sampleDocCount > 20:
            return
        for key,value in iteritems(eventJSON):
            if not key in self.schema:
                self.schema[key] = self.inferType(value)
        self.sampleDocCount = self.sampleDocCount + 1 
    
    def doGetNextData(self):
        msgs = []
        msg = self.consumer.poll(1)
        if msg is not None and msg.error() is None:
            jsonValue = json.loads(msg.value())
            self.inferSchema(json.loads(msg.value()))
            msgs.append(jsonValue)
        return msgs
    
    def close(self):
        self.consumer.close()