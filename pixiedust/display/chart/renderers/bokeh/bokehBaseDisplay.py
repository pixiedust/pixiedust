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

from pixiedust.display.display import CellHandshake
from pixiedust.display.chart.renderers import PixiedustRenderer
from pixiedust.utils import Logger,cache
from ..baseChartDisplay import BaseChartDisplay
from six import with_metaclass
from abc import abstractmethod, ABCMeta
from bokeh.plotting import figure, output_notebook
from bokeh.models.tools import *
import pkg_resources
from bokeh.palettes import viridis, magma, plasma, linear_palette, Spectral9, d3

try:
    from bokeh.embed import components as notebook_div
except ImportError:
    from bokeh.io import notebook_div

@PixiedustRenderer(rendererId="bokeh")
@Logger()
class BokehBaseDisplay(with_metaclass(ABCMeta, BaseChartDisplay)):
    CellHandshake.addCallbackSniffer( lambda: "{'nostore_bokeh':!!window.Bokeh}")

    #get the bokeh version
    try:
        bokeh_version = pkg_resources.get_distribution("bokeh").parsed_version._version.release
    except:
        bokeh_version = None
        self.exception("Unable to get bokeh version")

    def __init__(self, options, entity, dataHandler=None):
        super(BokehBaseDisplay,self).__init__(options,entity,dataHandler)
        #no support for orientation
        self.no_orientation = True
    
    """
    Default implementation for creating a chart object.
    """
    def createBokehChart(self):
        return figure()

    def getPreferredOutputWidth(self):
        return super(BokehBaseDisplay,self).getPreferredOutputWidth() * 0.92

    def get_common_figure_options(self):
        options = {}
        x_fields = self.getKeyFields()
        if len(x_fields) == 1 and (
            self.options.get("timeseries", 'false') == 'true' or self.dataHandler.isDateField(x_fields[0])
            ):
            options["x_axis_type"] = "datetime"
        elif self.getBooleanOption("logx", False):
            options["x_axis_type"] = "log"

        if self.getBooleanOption("logy", False):
            options["y_axis_type"] = "log"        
        return options

    @cache(fieldName="_loadJS")
    def getLoadJS(self):
        loadJS = self._load_notebook_html(hide_banner=True)
        return loadJS

    def colorPalette(self, size=None):
        # https://bokeh.pydata.org/en/latest/docs/reference/palettes.html
        # https://bokeh.pydata.org/en/latest/docs/reference/colors.html
        color = list(d3['Category10'][10]) # [ 'orangered', 'cornflowerblue',  ]
        # color = list(Spectral9).reverse()
        if size is None:
            return color
        elif size <= len(color):
            return color[0:size]
        elif size <= 256:
            return linear_palette(plasma(256), size)
        else:
            return linear_palette(plasma(256) + viridis(256) + magma(256), size)

    def doRenderChart(self):        
        def genMarkup(chartFigure):
            s = chartFigure[0] if isinstance(chartFigure, tuple) else chartFigure
            d = chartFigure[1] if isinstance(chartFigure, tuple) else ''
            return self.env.from_string("""
                    <script class="pd_save">
                    function setChartScript() {{
                        if (!window.Bokeh) {{
                            setTimeout(setChartScript, 250)
                        }} else {{
                            var d = document.getElementById("pd-bkchartdiv-{p}")
                            if (d){{
                                var el = document.createElement('div')
                                el.innerHTML = `{chartScript}`
                                var chartscript = el.childNodes[1]
                                var s = document.createElement("script")
                                s.innerHTML = chartscript.innerHTML
                                d.parentNode.insertBefore(s, d)
                            }}
                        }}
                    }}
                    if (!window.Bokeh && !window.autoload){{
                        window.autoload=true;
                        {loadJS}
                    }}
                    setChartScript()
                    </script>
                    <div style="padding:5px" id="pd-bkchartdiv-{p}">{chartDiv}</div>
                    {{%for message in messages%}}
                        <div>{{{{message}}}}</div>
                    {{%endfor%}}
                """.format(chartScript=s.replace('</script>', '<\/script>'), chartDiv=d, loadJS=self.getLoadJS(), p=self.getPrefix())
            ).render(messages=self.messages)

        minBkVer = (0,12,9)
        if BokehBaseDisplay.bokeh_version < minBkVer:
            raise Exception("""
                <div>Incorrect version of Bokeh detected. Expected {0} or greater, got {1}</div>
                <div>Please upgrade by using the following command: <b>!pip install --user --upgrade bokeh</b></div>
            """.format(minBkVer, BokehBaseDisplay.bokeh_version))
        clientHasBokeh = self.options.get("nostore_bokeh", "false") == "true"
        if not clientHasBokeh:          
            output_notebook(hide_banner=True)
        charts = self.createBokehChart()

        if not isinstance(charts, list):
            # charts.add_tools(ResizeTool())
            #bokeh 0.12.5 has a non backward compatible change on the title field. It is now of type Title
            #following line is making sure that we are still working with 0.12.4 and below
            if hasattr(charts, "title") and hasattr(charts.title, "text"):
                charts.title.text = self.options.get("title", "")
            else:
                charts.title = self.options.get("title", "")
            charts.plot_width = int(self.getPreferredOutputWidth() - 10 )
            charts.plot_height = int(self.getPreferredOutputHeight() - 10  )
            charts.grid.grid_line_alpha=0.3
            return genMarkup(notebook_div(charts))
        else:
            from bokeh.layouts import gridplot
            ncols = 2
            nrows = len(charts)/2 + len(charts)%2
            
            w = self.getPreferredOutputWidth()/ncols if len(charts) > 1 else self.getPreferredOutputWidth()
            h = w * self.getHeightWidthRatio() if len(charts) > 1 else self.getPreferredOutputHeight()
            for chart in charts:
                chart.plot_width = int(w - 5)
                chart.plot_height = int (h - 5)

            return genMarkup(notebook_div(gridplot(charts, ncols=ncols)))


    # no longer part of bokeh
    #  https://github.com/bokeh/bokeh/pull/6928#issuecomment-329040653
    #  https://www.bvbcode.com/code/9xhgwcsf-2674609
    def _load_notebook_html(self, resources=None, hide_banner=False, load_timeout=5000):
        from bokeh.core.templates import AUTOLOAD_NB_JS
        from bokeh.util.serialization import make_id
        from bokeh.resources import CDN
    
        if resources is None:
            resources = CDN
    
        element_id = make_id()
    
        js = AUTOLOAD_NB_JS.render(
            elementid = '' if hide_banner else element_id,
            js_urls  = resources.js_files,
            css_urls = resources.css_files,
            js_raw   = resources.js_raw,
            css_raw  = resources.css_raw_str,
            force    = 1,
            timeout  = load_timeout
        )
    
        return js