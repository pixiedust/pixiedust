from .connectionWidget import ConnectionWidget
from pixiedust.display.app import *
from pixiedust.services.serviceManager import *
from pixiedust.utils import Logger
from pyspark import *
from pyspark.sql import *
from xml.sax.saxutils import escape
import base64
import json
import requests

view_dbs = '0'
view_db = '1'
view_db_all_docs = '2'
view_db_all_docs_page = '3'
view_db_design_docs = '4'
view_db_query = '5'
view_db_query_results = '6'
view_db_query_results_page = '7'
view_db_search = '8'
view_db_search_results = '9'
view_db_search_results_page = '10'
view_db_view = '11'
view_db_view_page = '12'
view_generate_dataframe_all_docs = '13'
view_generate_dataframe_query = '14'
view_generate_dataframe_search = '15'
view_generate_dataframe_view = '16'


@PixieApp
@Logger()
class CloudantBrowser(ConnectionWidget):

    def get_data_frame(self):
        return self.df

    @route()
    def default(self):
        return """<div pd_widget="DataSourcesList"/>"""

    @route(selectedConnection='*')
    def start(self):
        connection = getConnection('cloudant', self.selectedConnection)
        credentials = json.loads(connection['PAYLOAD'])['credentials']
        self.spark_session = None
        self.sql_context = None
        self.host = credentials['host']
        self.protocol = credentials.get('protocol', 'https')
        self.port = credentials.get('port', 443)
        self.username = credentials['username']
        self.password = credentials['password']
        self.selectedConnection = None
        return self._view_dbs()

    @route(view=view_dbs)
    def _view_dbs(self):
        output = """
<div class="row">
    <div class="col-sm-10" style="padding: 10px;">
        <p><a href="#" pd_options="view=None">Back</a></p>
        <h3>Databases</h3>
"""
        self.all_docs_limit = 5
        self.all_docs_skip = 0
        self.query = None
        self.query_limit = 5
        self.query_skip = 0
        self.search_query = None
        self.search_limit = 5
        self.search_max_limit = 200
        self.search_skip = 0
        self.search_bookmark = None
        self.search_prev_bookmark = None
        self.view_name = None
        self.view_limit = 5
        self.view_skip = 0
        dbs = self.get_all_dbs(self.host, self.username, self.password)
        for db in dbs:
            output += '<p>'
            output += '<h4 style="margin: 0px"><a href="#" pd_options="view={}">{}'.format(view_db, db)
            output += '<pd_script>self.db="{}"</pd_script>'.format(db)
            output += '</a></h4>'
            output += '</p>'
        output += """
    </div>
</div>
"""
        return output

    @route(view=view_db)
    def _view_db(self):
        search_index_html = ''
        view_list_html = ''
        response = self.get_design_docs(self.host, self.username, self.password, self.db, -1)
        if 'rows' in response.keys():
            all_design_docs = map(lambda x: x['doc'], response['rows'])
            search_index_html = self.get_db_search_index_list_html(all_design_docs)
            view_list_html = self.get_db_view_list_html(all_design_docs)
        return """
<div class="row">
    <div class="col-sm-2" style="padding: 10px;">
        <p><a href="#" pd_options="view=""" + view_dbs + """">Back</a></p>
        <b><h3>""" + self.db + """</h3></b>
        <p>
            <h4 style="margin: 0px">
                <a href="#">All Documents
                    <target pd_target="target{{prefix}}" pd_options="view=""" + view_db_all_docs + """" />
                </a>              
            </h4>
        </p>
         <p>
            <h4 style="margin: 0px">
                <a href="#">Query
                    <target pd_target="target{{prefix}}" pd_options="view=""" + view_db_query + """" />
                </a>
            </h4>
        </p>
        <p>
            <h4 style="margin: 0px">
                <a href="#">Design Documents
                    <target pd_target="target{{prefix}}" pd_options="view=""" + view_db_design_docs + """" />
                </a>
            </h4>
        </p>
""" + search_index_html + """
""" + view_list_html + """
    </div>
    <div id="target{{prefix}}" class="col-sm-10" style="padding: 0px 10px 0px 30px;">
    </div>
</div>
"""

    def get_db_search_index_list_html(self, all_design_docs):
        return self.get_db_ddoc_list_html(all_design_docs, 'Search Indexes', 'indexes', 'search_doc', 'search_index', view_db_search)

    def get_db_view_list_html(self, all_design_docs):
        return self.get_db_ddoc_list_html(all_design_docs, 'Views', 'views', 'view_doc', 'view_name', view_db_view)

    def get_db_ddoc_list_html(self, all_design_docs, title, design_doc_type, doc_var_name, type_var_name, route_name):
        html = ''
        docs = []
        for doc in all_design_docs:
            if design_doc_type in doc.keys():
                docs.append(doc)
        if len(docs) > 0:
            html += """
<p><h4 style="margin: 0px">""" + title + """</h3></p>
"""
            i = -1
            for doc in docs:
                i = i + 1
                html += """
<p>
    <a href="#""" + design_doc_type + str(i) + """-{{prefix}}" data-toggle="collapse" style="text-decoration: none;"><h4 style="margin: 0px"><b>""" + doc['_id'] + """</b></h4></a>
    <div id=\"""" + design_doc_type + str(i) + """-{{prefix}}" class="collapse in" style="padding-top: 10px;">
"""
                for key in doc[design_doc_type]:
                    html += """
        <p>
            <h4 style="margin-top: 0px; margin-left: 20px;">
                <a href="#">""" + key + """
                    <target pd_target="target{{prefix}}" pd_options="view=""" + route_name + """" />
                    <pd_script>self.""" + doc_var_name + """='""" + doc['_id'][len('_design/'):] + """'
self.""" + type_var_name + """='""" + key + """'</pd_script>
                </a>
            </h4>
        </p>
"""
            html += """
    </div>
</p>"""
        return html

    @route(view=view_db_all_docs)
    def _view_all_docs(self):
        self.all_docs_skip = 0
        output = self.get_dialog_chrome_top('All Documents', None)
        output += """
<div class="row">
    <div id="target2{{prefix}}">""" + self._view_all_docs_page() + """</div>
</div>
"""
        output += self.get_dialog_chrome_bottom()
        return output

    @route(view=view_db_all_docs_page)
    def _view_all_docs_page(self):
        response = self.get_all_docs(self.host, self.username, self.password, self.db, self.all_docs_limit, self.all_docs_skip)
        if 'rows' in response.keys() and len(response['rows']) > 0:
            output = self.format_docs(map(lambda row: row['doc'], response['rows']))
            # previous/next buttons
            prev_skip = self.all_docs_skip
            next_skip = self.all_docs_skip
            if 'total_rows' in response.keys() and response['total_rows'] > (self.all_docs_skip + self.all_docs_limit):
                next_skip = next_skip + self.all_docs_limit
            if prev_skip > 0:
                prev_skip = prev_skip - self.all_docs_limit
            show_next_button = (next_skip > self.all_docs_skip)
            show_prev_button = (prev_skip < self.all_docs_skip)
            if show_prev_button or show_next_button:
                output += """
<div style="margin-top: 10px;">"""
                if show_prev_button:
                    output +="""
    <button type="submit" class="btn btn-info">Previous
        <target pd_target="target2{{prefix}}" pd_options="view=""" + view_db_all_docs_page + """" />
        <pd_script>self.all_docs_skip=""" + str(prev_skip) + """</pd_script>
    </button>"""
                if show_next_button:
                    output +="""
    <button type="submit" class="btn btn-info">Next
        <target pd_target="target2{{prefix}}" pd_options="view=""" + view_db_all_docs_page + """" />
        <pd_script>self.all_docs_skip=""" + str(next_skip) + """</pd_script>
    </button>"""
                output += '<span style="padding-left: 5px"><b>{} to {} of {}</b></span>'.format(self.all_docs_skip+1, self.all_docs_skip+len(response['rows']), response['total_rows'])
                output += """
</div>"""
            output += self.get_dataframe_button(view_generate_dataframe_all_docs, 'target2')
        else:
            output = """<p><b>No documents found.</b></p>"""
            output += self.get_dataframe_button(None, None)
        return output

    @route(view=view_db_design_docs)
    def _view_design_docs(self):
        output = self.get_dialog_chrome_top('Design Documents', None)
        output += """
<div class="row">
    <div id="target2{{prefix}}">"""
        response = self.get_design_docs(self.host, self.username, self.password, self.db, -1)
        if 'rows' in response.keys():
            output += self.format_docs(map(lambda row: row['doc'], response['rows']))
        else:
            output = """<p><b>No documents found.</b></p>"""
        output += """
    </div>
</div>"""
        output += self.get_dialog_chrome_bottom()
        return output

    @route(view=view_db_query)
    def _view_query(self):
        if self.query is None:
            self.query ="""
{
  "selector": {"_id": {"$gt": 0}},
  "fields": ["_id", "_rev"],
  "sort": [{"_id": "asc"}]
}"""
        self.query_skip = 0
        output = self.get_dialog_chrome_top('Query', None)
        output += """
<div class="row">
    <div class="form-group">
        <textarea rows="6" class="form-control" id="query{{prefix}}" style="font-family: monospace;">""" + self.query + """</textarea>
    </div>
    <div class="form-group">  
        <button type="submit" class="btn btn-primary" pd_refresh>Go
            <target pd_target="target2{{prefix}}" pd_options="view=""" + view_db_query_results + """" />
            <pd_script>self.query="$val(query{{prefix}})"</pd_script>
        </button>
    </div>
</div>
<div class="row">
    <div id="target2{{prefix}}"></div>
</div>
"""
        output += self.get_dialog_chrome_bottom()
        return output

    @route(view=view_db_query_results)
    def _view_query_results(self):
        self.query_skip = 0
        return self._view_query_results_page()

    @route(view=view_db_query_results_page)
    def _view_query_results_page(self):
        self.query = self.query.replace('&quot;', '"')
        response = self.run_query(self.host, self.username, self.password, self.db,
                                  self.query, self.query_limit, self.query_skip)
        if 'docs' in response.keys() and len(response['docs']) > 0:
            output = self.format_docs(response['docs'])
            # previous/next buttons
            prev_skip = self.query_skip
            next_skip = self.query_skip
            if len(response['docs']) >= self.query_limit:
                next_skip = next_skip + self.query_limit
            if prev_skip > 0:
                prev_skip = prev_skip - self.query_limit
            show_next_button = (next_skip > self.query_skip)
            show_prev_button = (prev_skip < self.query_skip)
            if show_prev_button or show_next_button:
                output += """
<div style="margin-top: 10px;">"""
                if show_prev_button:
                    output +="""
    <button type="submit" class="btn btn-info">Previous
        <target pd_target="target2{{prefix}}" pd_options="view=""" + view_db_query_results_page + """" />
        <pd_script>self.query_skip=""" + str(prev_skip) + """</pd_script>
    </button>"""
                if show_next_button:
                    output +="""
    <button type="submit" class="btn btn-info">Next
        <target pd_target="target2{{prefix}}" pd_options="view=""" + view_db_query_results_page + """" />
        <pd_script>self.query_skip=""" + str(next_skip) + """</pd_script>
    </button>"""
                output += '<span style="padding-left: 5px"><b>{} to {}</b></span>'.format(self.query_skip+1, self.query_skip+len(response['docs']))
                output += """
</div>"""
            output += self.get_dataframe_button(view_generate_dataframe_query, 'target2')
        else:
            output = """<b>No documents found.</b>"""
            output += self.get_dataframe_button(None, None)
        return output

    @route(view=view_db_search)
    def _view_search(self):
        if self.search_query is None:
            self.search_query = ''
        self.search_bookmark = None
        self.search_prev_bookmark=None
        output = self.get_dialog_chrome_top('Search', '{}/{}'.format(self.search_doc, self.search_index))
        output += """
<div class="row">
    <div class="form-group">
        <input type="text" class="form-control" id="search{{prefix}}" value="{{self.search_query}}" />
    </div>
    <div class="form-group">
        <button type="submit" class="btn btn-primary" pd_refresh>Go
            <target pd_target="target2{{prefix}}" pd_options="view=""" + view_db_search_results + """" />
            <pd_script>self.search_query="$val(search{{prefix}})"</pd_script>
        </button>
    </div>
</div>
<div class="row">
    <div id="target2{{prefix}}"></div>
</div>
"""
        output += self.get_dialog_chrome_bottom()
        return output

    @route(view=view_db_search_results)
    def _view_search_results(self):
        self.search_bookmark = None
        self.search_skip = 0
        return self._view_search_results_page()

    @route(view=view_db_search_results_page)
    def _view_search_results_page(self):
        response = self.run_search(self.host, self.username, self.password, self.db,
                                   self.search_doc, self.search_index, self.search_query,
                                   self.search_limit, self.search_bookmark)
        if 'rows' in response.keys() and len(response['rows']) > 0:
            output = self.format_docs(map(lambda x: x['doc'], response['rows']))
            # previous/next buttons
            if 'bookmark' in response.keys() and len(response['rows']) >= self.search_limit:
                next_bookmark = response['bookmark']
            else:
                next_bookmark = None
            if self.search_bookmark is not None or next_bookmark is not None:
                output += """
<div style="margin-top: 10px;">"""
                if self.search_bookmark is not None:
                    if self.search_prev_bookmark is None:
                        prev_bookmark_str = 'None'
                    else:
                        prev_bookmark_str = '"{}"'.format(self.search_prev_bookmark)
                    output +="""
    <button type="submit" class="btn btn-info">Previous
        <target pd_target="target2{{prefix}}" pd_options="view=""" + view_db_search_results_page + """" />
        <pd_script>self.search_bookmark=""" + prev_bookmark_str + """
self.search_skip=""" + str(self.search_skip - self.search_limit) + """</pd_script>
    </button>"""
                if next_bookmark is not None:
                    if self.search_bookmark is None:
                        prev_bookmark_str = 'None'
                    else:
                        prev_bookmark_str = '"{}"'.format(self.search_bookmark)
                    if next_bookmark is None:
                        next_bookmark_str = 'None'
                    else:
                        next_bookmark_str = '"{}"'.format(next_bookmark)
                    output +="""
    <button type="submit" class="btn btn-info">Next
        <target pd_target="target2{{prefix}}" pd_options="view=""" + view_db_search_results_page + """" />
        <pd_script>self.search_prev_bookmark=""" + prev_bookmark_str + """
self.search_bookmark=""" + next_bookmark_str + """
self.search_skip=""" + str(self.search_skip + self.search_limit) + """</pd_script>
    </button>"""
                output += '<span style="padding-left: 5px"><b>{} to {}</b></span>'.format(self.search_skip+1, self.search_skip+len(response['rows']))
                output += """
</div>"""
            output += self.get_dataframe_button(view_generate_dataframe_search, 'target2')
        else:
            output = """<b>No documents found.</b>"""
            output += self.get_dataframe_button(None, None)
        return output

    @route(view=view_db_view)
    def _view_view(self):
        self.view_skip = 0
        output = self.get_dialog_chrome_top('View', '{}/{}'.format(self.view_doc, self.view_name))
        output += """
<div class="row">
    <div id="target2{{prefix}}">""" + self._view_view_page() + """</div>
</div>
"""
        output += self.get_dialog_chrome_bottom()
        return output

        return self._view_view_page()

    @route(view=view_db_view_page)
    def _view_view_page(self):
        response = self.get_view(self.host, self.username, self.password, self.db,
                                 self.view_doc, self.view_name, self.view_limit, self.view_skip)
        if 'rows' in response.keys():
            output = self.format_docs(map(lambda x: x['doc'], response['rows']))
            # previous/next buttons
            prev_skip = self.view_skip
            next_skip = self.view_skip
            if 'total_rows' in response.keys() and response['total_rows'] > (self.view_skip + self.view_limit):
                next_skip = next_skip + self.view_limit
            if prev_skip > 0:
                prev_skip = prev_skip - self.view_limit
            show_next_button = (next_skip > self.view_skip)
            show_prev_button = (prev_skip < self.view_skip)
            if show_prev_button or show_next_button:
                output += """
<div style="margin-top: 10px;">"""
                if show_prev_button:
                    output +="""
    <button type="submit" class="btn btn-info">Previous
        <target pd_target="target2{{prefix}}" pd_options="view=""" + view_db_view_page + """" />
        <pd_script>self.view_skip=""" + str(prev_skip) + """</pd_script>
    </button>"""
                if show_next_button:
                    output +="""
    <button type="submit" class="btn btn-info">Next
        <target pd_target="target2{{prefix}}" pd_options="view=""" + view_db_view_page + """" />
        <pd_script>self.view_skip=""" + str(next_skip) + """</pd_script>
    </button>"""
                output += '<span style="padding-left: 5px"><b>{} to {} of {}</b></span>'.format(self.view_skip+1, self.view_skip+len(response['rows']), response['total_rows'])
                output += """
</div>"""
            output += self.get_dataframe_button(view_generate_dataframe_view, 'target2')
        else:
            output = """<p><b>No documents found.</b></p>"""
            output += self.get_dataframe_button(None, None)
        output += self.get_dialog_chrome_bottom()
        return output

    @route(view=view_generate_dataframe_all_docs)
    def _generate_dataframe_all_docs(self):
        self.df = self.get_dataframe_reader().load(self.db)
        output = 'DataFrame generated. Access by calling app.get_data_frame()'.format(self.db)
        return """
<p><b>""" + output + """</b></p>
"""

    @route(view=view_generate_dataframe_query)
    def _generate_dataframe_query(self):
        response = self.run_query(self.host, self.username, self.password, self.db, self.query, -1, 0)
        if 'docs' in response.keys():
            self.df = self.get_dataframe_builder().createDataFrame(response['docs'])
            output = 'DataFrame generated. Access by calling app.get_data_frame()'.format(self.db)
        else:
            output = 'No documents found.'
        return """
<p><b>""" + output + """</b></p>
"""

    @route(view=view_generate_dataframe_search)
    def _generate_dataframe_search(self):
        docs = []
        bookmark = None
        while True:
            response = self.run_search(self.host, self.username, self.password, self.db,
                                       self.search_doc, self.search_index, self.search_query,
                                       self.search_max_limit, bookmark)
            if 'rows' in response.keys():
                if len(response['rows']) == 0:
                    break
                docs.extend(map(lambda x: x['doc'], response['rows']))
                if 'bookmark' in response.keys():
                    bookmark = response['bookmark']
                else:
                    break
            else:
                break
        if len(docs) > 0:
            self.df = self.get_dataframe_builder().createDataFrame(docs)
            output = 'DataFrame generated. Access by calling app.get_data_frame()'.format(self.db)
        else:
            output = 'No documents found.'
        return """
<p><b>""" + output + """</b></p>"""

    @route(view=view_generate_dataframe_view)
    def _generate_dataframe_view(self):
        self.df = self.get_dataframe_reader() \
            .option("index", "_design/{}/_view/{}".format(self.view_doc, self.view_name)) \
            .load(self.db)
        output = 'DataFrame generated. Access by calling app.get_data_frame()' \
            .format(self.db, self.view_doc, self.view_name)
        return """
<p><b>""" + output + """</b></p>
"""

    def get_all_dbs(self, host, username, password):
        url = '{0}://{1}/_all_dbs'.format(self.protocol, host)
        r = requests.get(url, headers={
            'Authorization': 'Basic {}'.format(base64.b64encode('{}:{}'.format(username, password))),
            'Accept': 'application/json'
        })
        return r.json()

    def get_all_docs(self, host, username, password, db, limit, skip):
        url = '{}://{}/{}/_all_docs?include_docs=true'.format(self.protocol, host,db)
        if limit > 0:
            url = '{}&limit={}'.format(url,limit)
        if skip > 0:
            url = '{}&skip={}'.format(url,skip)
        r = requests.get(url, headers={
            'Authorization': 'Basic {}'.format(base64.b64encode('{}:{}'.format(username, password))),
            'Accept': 'application/json'
        })
        return r.json()

    def get_design_docs(self, host, username, password, db, limit):
        url = '{}://{}/{}/_all_docs?startkey="_design/"&endkey="_design0"&include_docs=true'.format(self.protocol, host,db)
        if limit > 0:
            url = '{}&limit={}'.format(url,limit)
        r = requests.get(url, headers={
            'Authorization': 'Basic {}'.format(base64.b64encode('{}:{}'.format(username, password))),
            'Accept': 'application/json'
        })
        return r.json()

    def run_query(self, host, username, password, db, query, limit, skip):
        if limit > 0:
            query_json = json.loads(query)
            query_json['limit'] = limit
            if skip > 0:
                query_json['skip'] = skip
            query = json.dumps(query_json)
        url = '{}://{}/{}/_find'.format(self.protocol, host, db)
        r = requests.post(url, data=query, headers={
            'Authorization': 'Basic {}'.format(base64.b64encode('{}:{}'.format(username, password))),
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        return r.json()

    def run_search(self, host, username, password, db, design_doc, index, query, limit, bookmark):
        url = '{}://{}/{}/_design/{}/_search/{}?q={}&include_docs=true'.format(self.protocol, host, db, design_doc, index, query)
        if limit > 0:
            url = '{}&limit={}'.format(url,limit)
            if bookmark:
                url = '{}&bookmark={}'.format(url,bookmark)
        r = requests.get(url, headers={
            'Authorization': 'Basic {}'.format(base64.b64encode('{}:{}'.format(username, password))),
            'Accept': 'application/json'
        })
        return r.json()

    def get_view(self, host, username, password, db, design_doc, view, limit, skip):
        url = '{}://{}/{}/_design/{}/_view/{}?include_docs=true'.format(self.protocol, host, db, design_doc, view)
        if limit > 0:
            url = '{}&limit={}'.format(url, limit)
        if skip > 0:
            url = '{}&skip={}'.format(url, skip)
        r = requests.get(url, headers={
            'Authorization': 'Basic {}'.format(base64.b64encode('{}:{}'.format(username, password))),
            'Accept': 'application/json'
        })
        return r.json()

    def format_docs(self, docs):
        output = ''
        i = -1
        for doc in docs:
            i = i + 1
            j = 0
            content = json.dumps(doc, indent=2, sort_keys=True).encode('utf-8')
            content = self.escape_html(content)
            title = '<pre style="font-size: 9pt;">' + doc['_id'] + ' {</pre>'
            for key in sorted(doc.keys()):
                if key == '_id' or key == '_rev' or isinstance(doc[key], list):
                    continue
                else:
                    try:
                        value = str(doc[key].encode('utf-8'))
                        if len(value) > 20:
                            value = value[0:20] + '...'
                        title += '<pre style="font-size: 9pt;">  "{}": "{}"</pre>'.format(key, value)
                        j = j + 1
                        if j >= 3:
                            break
                    except:
                        pass
            title += '<pre>   ...</pre>'
            output += '<div style="margin-top: 5px;">'
            output += '<a href="#doc' + str(i) + '-{{prefix}}" style="text-decoration: none;" data-toggle="collapse">' + title + '</a>'
            output += '<div id="doc' + str(i) + '-{{prefix}}" class="collapse">'
            output += '<pre style="margin: 0px 20px 0px 20px; padding: 10px; font-size: 9pt; background-color: white; max-height: 200px; white-space: pre; overflow: scroll; border-style: solid; border-radius: 2px; border-width: 1px; border-color: #aaa;">{}</pre>'.format(content)
            output += '</div>'
            output += '<a href="#doc' + str(i) + '-{{prefix}}" style="text-decoration: none;" data-toggle="collapse"><pre style="font-size: 9pt;">}</pre></a>'
            output += '</div>'
        return output

    def get_dialog_chrome_top(self, title, subtitle):
        subtitle_str = ''
        if subtitle:
            subtitle_str = ' ({})'.format(subtitle)
        return """
<div class="row" style="padding: 0x; margin: 10px; border-style: solid; border-radius: 4px 4px 0 0; border-width: 1px; border-color: #ddd;">
    <h4 style="padding: 0px 0px 10px 10px;">""" + title + subtitle_str + """</h4>
    <div id="target{{prefix}}" class="row" style="padding: 15px; margin-bottom: 0px; background-color: #f5f5f5;">"""

    def get_dialog_chrome_bottom(self):
        return """
    </div>
</div>"""
        return output

    def get_dataframe_button(self, generate_dataframe_view, generate_dataframe_target):
        output = ''
        if generate_dataframe_view is not None:
            output += """
<hr style="border: 1px solid #ddd;">
<button type="submit" class="btn btn-primary" data-dismiss="modal">Generate DataFrame
    <target pd_target=\"""" + generate_dataframe_target + """{{prefix}}" pd_options="view=""" + generate_dataframe_view + """" />
</button>"""
        return output

    def escape_html(self, text):
        return escape(text)

    def get_dataframe_reader(self):
        if self.sql_context is None and self.spark_session is None:
            self.get_dataframe_builder()
        if self.spark_session is not None:
            return self.spark_session.read.format("com.cloudant.spark")
        else:
            return self.sql_context.read.format("com.cloudant.spark") \
                .option("cloudant.host", self.host) \
                .option("cloudant.username", self.username) \
                .option("cloudant.password", self.password)

    def get_dataframe_builder(self):
        if self.sql_context is None and self.spark_session is None:
            spark_context = SparkContext.getOrCreate()
            spark_major_version = int(spark_context.version[0:spark_context.version.index('.')])
            if spark_major_version >= 2:
                self.spark_session = SparkSession.builder \
                    .config("cloudant.host", self.host) \
                    .config("cloudant.username", self.username) \
                    .config("cloudant.password", self.password) \
                    .getOrCreate()
            else:
                self.sql_context = SQLContext(spark_context)
        if self.spark_session is not None:
            return self.spark_session
        else:
            return self.sql_context
