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

from gateway.notebookMgr import ast_parse, get_symbol_table, RewriteGlobals
import astunparse
from nose.tools import assert_equals


code_map = [
{
    "src": """
var1 = foo()
for v in someList:
    var1 = bar(var1)
for v in someList:
    for k in deeperList:
        var1 = bar(var1)
""",
    "target": """
ns_var1 = foo()
for v in someList:
    ns_var1 = bar(ns_var1)
for v in someList:
    for k in deeperList:
        ns_var1 = bar(ns_var1)
"""
},{
    "src":"""
class Test():
    def foo(self):
        pass
a = Test()
a.foo()
""",
    "target":"""
class ns_Test():
    def foo(self):
        pass
ns_a = ns_Test()
ns_a.foo()
"""
}
]

def compare_multiline(src, target):
    assert_equals(
        "\n".join([l for l in src.split('\n') if l.strip()!='']), 
        "\n".join([l for l in target if l.strip()!=''])
    )

def test_rewrite():
    for code in code_map:
        symbols = get_symbol_table(ast_parse( code['src'] ) )
        rewrite_code = astunparse.unparse( RewriteGlobals(symbols, "ns_").visit(ast_parse(code['src'])) )
        compare_multiline(code["target"],rewrite_code.split('\n'))
