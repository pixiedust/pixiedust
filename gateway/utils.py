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
import re

def sanitize_traceback(data):
    """
    sanitize traceback returned in IPython msg and convert to html
    """
    if not isinstance(data, list):
        data = [data]

    def get_style(items):
        colors = {
            31: [(255, 0, 0), (128, 0, 0)],
            32: [(0, 255, 0), (0, 128, 0)],
            33: [(255, 255, 0), (128, 128, 0)],
            34: [(0, 0, 255), (0, 0, 128)],
            35: [(255, 0, 255), (128, 0, 128)],
            36: [(0, 255, 255), (0, 128, 128)],
        }
        color = [colors[c] for c in items if c in colors]
        bold = any([c for c in items if c in [1, 5]])

        color = "" if len(color) == 0 else "color:rgb{}".format(color[0][0] if not bold else color[0][1])
        bold = "" if not bold else "font-weight:bolder"
        return """{};{}""".format(color, bold)

    def escape(data):
        return data.replace("<", "&lt;").replace(">","&gt;")

    div = []
    for frame in data:
        lines = frame.split('\n')
        for line in lines:
            spans = []
            current_index = 0
            for m in [m for m in re.finditer(r"\x1b\[(.*?)([@-~])", line)]:
                style = ""
                if m.groups()[1] == "m":
                    items = ([0 if item == "" else int(item) for item in m.groups()[0].split(";")])
                    style = """style="{}" """.format(get_style(items))

                spans.append("<span {}>{}</span>".format(style, escape(line[current_index:m.span()[0]])))
                current_index = m.span()[1]
            spans.append("<span>{}</span>".format(escape(line[current_index:])))
            div.append("<div style='display: inline-flex;'>{}</div>".format("\n".join(spans)))

    return "<div style='border: 1px solid chartreuse;background: aliceblue'>{}</div>".format("\n".join(div))
