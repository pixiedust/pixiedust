# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2018
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
from pixiedust.utils import Logger
from pixiedust.display.datahandler import getDataHandler
from pixiedust.utils import *
from pixiedust.utils.dataFrameMisc import isPySparkDataFrame, isPandasDataFrame
from pixiedust.utils.environment import Environment

from pixiedust.utils.astParse import parse_function_call
from IPython.core.getipython import get_ipython

from pixiedust.utils.shellAccess import ShellAccess
from pixiedust.display.chart.options.baseOptions import BaseOptions
import json

@PixieApp
@Logger()
class FilterApp(BaseOptions):
    def get_custom_options(self):
        return { "runInDialog":"false" }

    def setup(self):
        BaseOptions.setup(self)

        self.filter_options = {}
        if self.run_options is not None and 'filter' in self.run_options:
            self.filter_options = json.loads(self.run_options['filter'])
    
        self.parent_prefix = self.parsed_command['kwargs']['prefix']
        self.fieldNamesAndTypes = self.get_field_names_and_types(True, True)
        self.fieldNames = self.get_field_names(True)

    def reset_data(self):
        self.df = self.parent_entity
        self.dfh = getDataHandler(None, self.df)

    def clear_filter(self, v):
        self.reset_data()
        self.filter_options = {}
        self.on_update()

    def get_new_options(self):
        return {
            "filter": json.dumps(self.filter_options)
        }

    @route()
    @templateArgs
    def main_screen(self): 
        self.reset_data()
        cleared = None
        cols = self.fieldNames
        filteredField = self.filter_options['field'] if 'field' in self.filter_options else ''

        if filteredField not in cols:
            filteredField = ''
            self.filter_options = {}
        
        return """
        <style>
        #columnselect{{prefix}}, #constraintsselect{{prefix}} { margin:0px; width:calc(100% - 10px); }
        .div-inline { display:inline-block;vertical-align:top } 
        .filter-heading {vertical-align:top;font-weight:500;margin-bottom:10px;}
        .filter-heading > span:last-of-type { font-size: small;font-weight: 300;display: inline-block;padding-left: 10px; }
        .form-inline select {vertical-align:top !important}
        .new-line {display:block !important} 
        .query-input { min-width: calc(100% - 10px); }
        input.form-control, .filter-clear { margin-right: 12px;}
        .stats .label {margin: 0 0.2em} 
        .filter-ui .label {font-weight:300} 
        .stats-table { width: 100%; } 
        .stats-table td { vertical-align:top; }
        .stats-table th { text-align:center; }
        .stats-table tr td:nth-child(2n) { text-align: left; }
        .panel-heading .data-toggle:before { font-family:fontAwesome; content:"\\f0da\\00a0\\00a0"; }
        .panel-heading .data-toggle[aria-expanded="true"]:before { font-family:fontAwesome; content:"\\f0d7\\00a0\\00a0"; }
        a.data-toggle, a.data-toggle:link, a.data-toggle:visited { text-decoration: none }
        #casematterscheck_{{prefix}}, regexcheck_{{prefix}} {margin: 0;}
        #df-stats-panel{{prefix}}, #regex-help-panel{{prefix}} { margin-bottom: 0; }
        #df-stats-panel{{prefix}} .panel-heading, #regex-help-panel{{prefix}} .panel-heading { font-size: 13px; padding: 9px 15px; }
        #df-stats-panel{{prefix}} .panel-body, #regex-help-panel{{prefix}} .panel-body { padding:0;max-height:240px;white-space:nowrap;overflow-y:scroll}
        #regex-help-panel{{prefix}} h3, #regex-help-panel{{prefix}} dt { margin-left: 10px}
        #regex-help-panel{{prefix}} dd { margin-left: 25px}
        </style>
        <div class="filter-ui">
            <div class="filter-heading panel-title">
                <span>Filter:</span>
                <span id="results{{prefix}}" class="no_loading_msg"></span>
            </div>
            
            <form class="form-inline row">
                <div class="form-group col-sm-2">
                    <select id="columnselect{{prefix}}" pd_options="field=$val(columnselect{{prefix}})" pd_target="constraints{{prefix}}" class="form-control filter-select" aria-label="select column">
                        <option value="--select-column--" disabled selected>Select a Field</option>
                    {%for col in cols %}
                        <option value="{{col}}">{{col}}</option>
                    {%endfor%}
                    </select>
                </div>
                <div class="form-group col-sm-10">
                    <div id="constraints{{prefix}}" class="no_loading_msg"></div>
                </div>
            </form>
        </div>
        <script>
        function filterInfo{{prefix}}() {
            var v = $('#manualvalue_{{prefix}}').val()
            if (v) {
                var r = $('#regexcheck_{{prefix}}').is(':checked') ? 'True' : 'False'
                var m = $('#casematterscheck_{{prefix}}').is(':checked') ? 'True' : 'False'
                var filtermsg = 'field: ' + $('#columnselect{{prefix}}').val() + ', constraint: ' + ($('#constraintsselect{{prefix}}').val() || 'None') + ', value: ' + v + ', casematters: ' + m + ', regex: ' + r
                $('#filterbutton{{this.parent_prefix}}').attr('title', 'Filter - ' + filtermsg)
                $('#results{{prefix}}').text(filtermsg)
                $('#filterbutton{{this.parent_prefix}}').css({
                    'background-color': 'orange',
                    'border-color': 'orange',
                    'color': 'white'
                })
            } else {
                clearFilterInfo{{prefix}}(true)
            }
        }
        function clearFilterInfo{{prefix}}(donotempty) {
            $('#filterbutton{{this.parent_prefix}}').attr('title', 'Filter')
            $('#results{{prefix}}').text('')
            $('#filterbutton{{this.parent_prefix}}').css({
                'background-color': '',
                'border-color': '',
                'color': ''
            })
            $('#manualvalue_{{prefix}}').val('')
            if (!donotempty) {
                $('#columnselect{{prefix}}').val('--select-column--')
                $('#constraints{{prefix}}').empty()
            }

            return ''
        }
        function valOnUpdate{{prefix}}() {
            filterInfo{{prefix}}()
            var v = $('#manualvalue_{{prefix}}').val()
            return v.replace(/\\\\/g, '\\\\\\\\')
        }
        if ('{{filteredField}}') {
            $('#columnselect{{prefix}}').val('{{filteredField}}').change()
        }
        </script>
        """
    
    @route(field="*")
    @templateArgs
    def colnamechange(self, field):
        # self.reset_data()
        filteredConstraint = self.filter_options['constraint'] if 'constraint' in self.filter_options else ''
        filteredValue = (self.filter_options['value'] if 'value' in self.filter_options else '').replace("\\", "\\\\")
        filteredRegex = self.filter_options['regex'] if 'regex' in self.filter_options else 'False'
        filteredCase = self.filter_options['case_matter'] if 'case_matter' in self.filter_options else 'False'

        isNumericField = self.dfh.isNumericField(field)
        if isNumericField and (filteredConstraint == 'None' or not filteredConstraint):
            filteredConstraint = 'equal_to'

        stats = ""
        controls = ""
        manualvalue = """
        <div class="form-group col-sm-4">
            <input class="form-control query-input" id="manualvalue_{{prefix}}" placeholder="Enter value">
        </div>
        """
        script = """
            $('#manualvalue_{{prefix}}').keydown(function(event){
                if (event.keyCode == 13) {
                    event.preventDefault()
                    return false
                }
            })
            if ('{{filteredConstraint}}') {
                $('#constraintsselect{{prefix}}').val('{{filteredConstraint}}')
            }
            if ('{{filteredValue}}') {
                $('#manualvalue_{{prefix}}').val('{{filteredValue}}')
            }
        """

        if not isNumericField:
            script += """
                if ('{{filteredRegex}}') {
                    $('#regexcheck_{{prefix}}').prop('checked', ('{{filteredRegex}}'.toLowerCase() === 'true'));
                }
                if ('{{filteredCase}}') {
                    $('#casematterscheck_{{prefix}}').prop('checked', ('{{filteredCase}}'.toLowerCase() === 'true'));
                }
            """
            controls = """
            <div class="form-group col-sm-2">
                <input type="checkbox" id="casematterscheck_{{prefix}}" value="casematters"> Case-sensitive<br/>
                <input type="checkbox" id="regexcheck_{{prefix}}" value="regex"> Regex
            </div>
              """
            stats += """
            <div class="form-group col-sm-4">
                <div id="regex-help-panel{{prefix}}" class="panel panel-default">
                    <div class="panel-heading">
                        <h4 class="panel-title " style="margin:0px">
                            <a data-toggle="collapse" class="data-toggle" href="#regex-help-{{prefix}}">Regex help</a>
                        </h4>
                    </div>
                    <div id="regex-help-{{prefix}}" class="panel-collapse collapse">
                        <div class="panel-body">
                            <h3>Character classes</h3>
                            <dt>[abc]</dt><dd>matches a or b, or c.</dd>
                            <dt>[^abc]</dt><dd>negation, matches everything except a, b, or c.</dd>
                            <dt>[a-c]</dt><dd>range, matches a or b, or c.</dd>
                            <dt>[a-c[f-h]]</dt><dd>union, matches a, b, c, f, g, h.</dd>
                            <dt>[a-c&&[b-c]]</dt><dd>intersection, matches b or c.</dd>
                            <dt>[a-c&&[^b-c]]</dt><dd>subtraction, matches a.</dd>

                            <h3>Predefined character classes</h3>
                            <dt>.</dt><dd>Any character.</dd>
                            <dt>&#92;d</dt><dd>A digit: [0-9]</dd>
                            <dt>&#92;D</dt><dd>A non-digit: [^0-9]</dd>
                            <dt>&#92;s</dt><dd>A whitespace character: [ &#92;t&#92;n&#92;x0B&#92;f&#92;r]</dd>
                            <dt>&#92;S</dt><dd>A non-whitespace character: [^&#92;s]</dd>
                            <dt>&#92;w</dt><dd>A word character: [a-zA-Z_0-9]</dd>
                            <dt>&#92;W</dt><dd>A non-word character: [^&#92;w]</dd>

                            <h3>Boundary matches</h3>
                            <dt>^</dt><dd>The beginning of a line.</dd>
                            <dt>$</dt><dd>The end of a line.</dd>
                            <dt>&#92;b</dt><dd>A word boundary.</dd>
                            <dt>&#92;B</dt><dd>A non-word boundary.</dd>
                            <dt>&#92;A</dt><dd>The beginning of the input.</dd>
                            <dt>&#92;G</dt><dd>The end of the previous match.</dd>
                            <dt>&#92;Z</dt><dd>The end of the input but for the final terminator, if any.</dd>
                            <dt>&#92;z</dt><dd>The end of the input.</dd>
                        </div>
                    </div>
                </div>
            </div>
            """
        
        else: # numeric field
            controls = """
            <div class="form-group col-sm-1">
            <select id="constraintsselect{{prefix}}" class="form-control filter-select col-3">
                <option value="less_than"> < </option>
                <option value="equal_to"> = </option>
                <option value="greater_than"> > </option>
            </select>
            </div>
            """

            # GENERATE A TABLE OF STATISTICS
            stats += """
            <div class="form-group col-sm-5">
                <div id="df-stats-panel{{prefix}}" class="panel panel-default">
                    <div class="panel-heading">
                        <h4 class="panel-title " style="margin:0px">
                            <a data-toggle="collapse" class="data-toggle" href="#df-stats-{{prefix}}">Statistics: <span style="font-weight: normal">{{field}}</span></a>
                        </h4>
                    </div>
                    <div id="df-stats-{{prefix}}" class="panel-collapse collapse">
                        <div class="panel-body">
            """

            stats += self.stats_table(field)

            stats += """
                        </div>
                    </div>
                </div>
            </div>
            """

        script += """
            filterInfo{{prefix}}()
        """
        submit = """
        <div class="form-group col-sm-1">
            <button type="button" class="btn btn-default btn-primary filter-submit" pd_options="field={{field}};constraint=None;val=$val(valOnUpdate{{prefix}});casematters=$val(casematterscheck_{{prefix}});regex=$val(regexcheck_{{prefix}})" pd_target="results{{prefix}}">Apply</button>
        </div>
        """
        if isNumericField:
            submit = """
            <div class="form-group col-sm-1">
                <button type="button" class="btn btn-default btn-primary filter-submit" pd_options="field={{field}};constraint=$val(constraintsselect{{prefix}});val=$val(valOnUpdate{{prefix}});casematters=False;regex=False" pd_target="results{{prefix}}">Apply</button>
            </div>
            """
        
        clear = """
        <div class="form-group col-sm-1">
            <button type="button" class="btn btn-default filter-clear" pd_script="self.clear_filter('$val(clearFilterInfo{{prefix}})')">Clear</button>
        </div>"""

        if not isNumericField:
            return '<div class="row">' + manualvalue + controls + submit + clear + stats + '<script>' + script + '</script></div>'
        else:
            return '<div class="row">' + controls + manualvalue + submit + clear + stats + '<script>' + script + '</script></div>'

    @route(field="*", constraint="*", casematters="*")
    def noqueryvalue(self, field, constraint, casematters): 
        # called when user submits without entering anything in the query <input>
        return self.compute(field, constraint, '', casematters, 'false')

    @route(field="*", constraint="*", val="*", casematters="*", regex="*")
    def compute(self, field, constraint, val, casematters, regex):
        isNumericField = self.dfh.isNumericField(field)
        if not val or not val.strip() or val.strip() == 'None':
            val = 'None'

        if isNumericField and constraint not in ['less_than', 'greater_than', 'equal_to']:
            return "<h4>A constraint is required</h4>"
        elif isNumericField and val != 'None' and not val.replace('.','',1).replace('-','',1).isdigit():
            return "<h4>A numeric value is required</h4>"
        else:
            self.filter_options = {
                "field": field,
                "constraint": constraint,
                "value": val.replace("\\", "\\\\"),
                "case_matter": casematters,
                "regex": regex
            }

            self.on_update()
            return "field: {}, constraint: {}, value: {}, casematters: {}, regex: {}".format(field, constraint, val, casematters, regex)

    def stats_table(self, field):
        self.summary_stats = []
        self.quantiles = []
        self.frequents = []
        
        if isPySparkDataFrame(self.df):
            statsdf = self.df.describe(field)
            lbls = ['count','mean','std','min','max']

            for i in [0,1,2,3,4]:
                if i == 0:
                    self.summary_stats.append((lbls[i], "{:.0f}".format(float(statsdf.collect()[i][1]))))
                else:
                    self.summary_stats.append((lbls[i], "{:.2f}".format(float(statsdf.collect()[i][1]))))
                    
            if Environment.sparkVersion == 2:
                lbls = ['2%','9%','25%','50%','75%','91%','98%']
                quants = self.df.approxQuantile(field, [.02, .09, .25, .50, .75, .91, .98], 0.1)
                for i, q in enumerate(quants):
                    self.quantiles.append((lbls[i] + "ile", "{:.2f}".format(q)))
                
            freqdf = self.df.stat.freqItems([field], 0.1)
            freqlist = freqdf.collect()[0][field+'_freqItems']
            stop = 5
            for i in freqlist:
                if stop > 0:
                    self.frequents.append(str(i))
                stop = stop - 1
        else:
            if not isPandasDataFrame(self.df):
                self.df = self.data_handler.entity
            if isPandasDataFrame(self.df):
                statsdf = self.df[field].describe([.02, .09, .25, .50, .75, .91, .98])
                lbls = ['count','mean','std','min','max']

                for i in range(0,len(lbls)):
                    if i == 0:
                        self.summary_stats.append((lbls[i], "{:.0f}".format(statsdf[i])))
                    else:
                        self.summary_stats.append((lbls[i], "{:.2f}".format(statsdf[lbls[i]])))

                lbls = ['2%','9%','25%','50%','75%','91%','98%']
                for i in range(0,len(lbls)):
                    self.quantiles.append((lbls[i] + "ile", "{:.2f}".format(statsdf[lbls[i]])))

                freqseries = self.df[field].value_counts()
                stop = 5
                for ix in freqseries.index:
                    if stop > 0:
                        self.frequents.append(str(ix))
                    stop = stop - 1
                
        summaryname = '<br>'.join(s[0] for s in self.summary_stats)
        summaryvalue = '<br>'.join(s[1] for s in self.summary_stats)
        quantname = '<br>'.join(q[0] for q in self.quantiles)
        quantvalue = '<br>'.join(q[1] for q in self.quantiles)
        freqvalue = '<br>'.join(f for f in self.frequents)

        table = """
            <table class="stats-table">
                <thead>
                    <tr>""" 
        table += "<th colspan='2'>Summary</th> <th colspan='2'>Quantiles</th> <th>Frequents</th>" if Environment.sparkVersion == 2 else "<th colspan='2'>Summary</th> <th>Frequents</th>"
        table += """
                    </tr>
                </thead>
                <tbody>
                    <tr>"""
        table += "<td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td>" if Environment.sparkVersion == 2 else "<td>{}</td> <td>{}</td> <td>{}</td>"
        table += """
                    </tr>
                </tbody>
            </table>"""
            
        if Environment.sparkVersion == 2:
            return table.format(summaryname, summaryvalue, quantname, quantvalue, freqvalue)
        else:
            return table.format(summaryname, summaryvalue, freqvalue)

    def on_update(self):
        return self.on_ok(avoid_metadata=False, override_keys=['filter'])
