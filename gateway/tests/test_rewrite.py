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
