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
'''
Provide easy access to the Shell user variables
Sample use:
    ShellAccess.sc => access to the SparkContext
    ShellAccess["sqlContext"] => access the SQLContext
    ShellAccess.myVar = "Hello" => set a new variable called myVar in the user namespace
'''
class ShellAccess(object):
    __metaclass__= type("",(type,),{
        "__getitem__":lambda cls, key: get_ipython().user_ns.get(key),
        "__setitem__":lambda cls, key,val: get_ipython().user_ns.update({key:val}),
        "__getattr__":lambda cls, key: get_ipython().user_ns.get(key),
        "__setattr__":lambda cls, key, val: get_ipython().user_ns.update({key:val}),
        "__iter__": lambda cls: iter(get_ipython().user_ns.keys())
    })

    @staticmethod
    def update(**kwargs):
        for key,val in kwargs.iteritems():
            Configuration[key]=val
