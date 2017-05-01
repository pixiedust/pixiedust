from .connectionWidget import ConnectionWidget
from pixiedust.display.app import *
from pixiedust.services.serviceManager import *
from pyspark.sql import SparkSession
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
view_db_search = '7'
view_db_search_results = '8'
view_db_view = '9'
view_db_view_page = '10'
view_generate_dataframe_all_docs = '11'
view_generate_dataframe_query = '12'
view_generate_dataframe_search = '13'
view_generate_dataframe_view = '14'


@PixieApp
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
        self.host = credentials['host']
        self.username = credentials['username']
        self.password = credentials['password']
        self.selectedConnection = None
        # return "HOST = " + self.host + "; USERNAME = " + self.username + "; PASSWORD = " + self.password
        return self._view_dbs()

    @route(view=view_dbs)
    def _view_dbs(self):
        output = ''
        self.all_docs_limit = 10
        self.all_docs_skip = 0
        self.query = None
        self.query_limit = 10
        self.query_skip = 0
        self.search_query = None
        self.search_limit = 10
        self.search_max_limit = 200
        self.search_bookmark = None
        self.search_prev_bookmark = None
        self.view_name = None
        self.view_limit = 10
        self.view_skip = 0
        sparkSession = SparkSession.builder \
            .config("cloudant.host", self.host) \
            .config("cloudant.username", self.username) \
            .config("cloudant.password", self.password) \
            .getOrCreate()
        dbs = self.get_all_dbs(self.host, self.username, self.password)
        for db in dbs:
            output += '<p>'
            output += '<a pd_options="view={}">{}'.format(view_db,db)
            output += '<pd_script>self.db="{}"</pd_script>'.format(db)
            output += '</a>'
            output += '</p>'
        return """
<div class="row">
    <div id="target{{prefix}}" style="padding-right:10px;">""" + output + """</div>
</div>
"""

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
    <div class="form-group col-sm-3" style="overflow-x: scroll;">
        <p>
            <b>""" + self.db + """</b>
        </p>
        <p>
            <button type="submit" class="btn btn-primary" pd_options="view=""" + view_dbs + """">Back
            </button>
        </p>
        <p>
            <a>All Documents
                <target pd_target="target{{prefix}}" pd_options="view=""" + view_db_all_docs + """" />
            </a>
        </p>
        <p>
            <a>Design Documents
                <target pd_target="target{{prefix}}" pd_options="view=""" + view_db_design_docs + """" />
            </a>
        </p>
        <p>
            <a>Query
                <target pd_target="target{{prefix}}" pd_options="view=""" + view_db_query + """" />
            </a>
        </p>""" + search_index_html + view_list_html + """
    </div>
    <div class="form-group col-sm-9" style="padding-left: 10px;">
        <div id="target{{prefix}}"></div>
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
<p><b>""" + title + """</b></p>
"""
            i = -1
            for doc in docs:
                i = i + 1
                html += """
<p>
    <a href="#""" + design_doc_type + str(i) + """-{{prefix}}" data-toggle="collapse">""" + doc['_id'] + """</a>
    <div id=\"""" + design_doc_type + str(i) + """-{{prefix}}" class="collapse" style="padding-top: 10px;">
"""
                for key in doc[design_doc_type]:
                    html += """
        <p>
            <a>""" + key + """
                <target pd_target="target{{prefix}}" pd_options="view=""" + route_name + """" />
                <pd_script>self.""" + doc_var_name + """='""" + doc['_id'][len('_design/'):] + """'
self.""" + type_var_name + """='""" + key + """'</pd_script>
            </a>
        </p>
"""
            html += """
    </div>
</p>"""
        return html

    @route(view=view_db_all_docs)
    def _view_all_docs(self):
        self.all_docs_skip = 0
        return self._view_all_docs_page()

    @route(view=view_db_all_docs_page)
    def _view_all_docs_page(self):
        response = self.get_all_docs(self.host, self.username, self.password, self.db, self.all_docs_limit, self.all_docs_skip)
        if 'rows' in response.keys():
            output = self.format_docs(map(lambda row: row['doc'], response['rows']), view_generate_dataframe_all_docs, 'target')
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
<p>"""
                if show_prev_button:
                    output +="""
    <button type="submit" class="btn btn-primary">Previous
        <target pd_target="target{{prefix}}" pd_options="view=""" + view_db_all_docs_page + """" />
        <pd_script>self.all_docs_skip=""" + str(prev_skip) + """</pd_script>
    </button>"""
                if show_next_button:
                    output +="""
    <button type="submit" class="btn btn-primary">Next
        <target pd_target="target{{prefix}}" pd_options="view=""" + view_db_all_docs_page + """" />
        <pd_script>self.all_docs_skip=""" + str(next_skip) + """</pd_script>
    </button>
</p>
"""
        else:
            output = """
<b>No documents found.</b>
"""
        return output

    @route(view=view_db_design_docs)
    def _view_design_docs(self):
        response = self.get_design_docs(self.host, self.username, self.password, self.db, -1)
        if 'rows' in response.keys():
            return self.format_docs(map(lambda row: row['doc'], response['rows']), None, None)
        else:
            return """
<b>No documents found.</b>
"""

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
        return """
<div class="row">
    <div class="form-group">
        <label for="query{{prefix}}" class="control-label col-sm-2">Query:</label>
        <textarea rows="6" class="form-control" id="query{{prefix}}">""" + self.query + """</textarea>
    </div>
    <div class="form-group">  
        <button type="submit" class="btn btn-primary">Go
            <target pd_target="target2{{prefix}}" pd_options="view=""" + view_db_query_results + """" />
            <pd_script>self.query=$val(query{{prefix}})</pd_script>
        </button>
    </div>
</div>
<div class="row">
    <div id="target2{{prefix}}"></div>
</div>
"""
    @route(view=view_db_query_results)
    def _view_query_results(self):
        self.query = self.query.replace('&quot;', '"')
        response = self.run_query(self.host, self.username, self.password, self.db,
                                  self.query, self.query_limit, self.query_skip)
        if 'docs' in response.keys():
            output = self.format_docs(response['docs'], view_generate_dataframe_query, 'target2')
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
<p>"""
                if show_prev_button:
                    output +="""
    <button type="submit" class="btn btn-primary">Previous
        <target pd_target="target2{{prefix}}" pd_options="view=""" + view_db_query_results + """" />
        <pd_script>self.query_skip=""" + str(prev_skip) + """</pd_script>
    </button>"""
                if show_next_button:
                    output +="""
    <button type="submit" class="btn btn-primary">Next
        <target pd_target="target2{{prefix}}" pd_options="view=""" + view_db_query_results + """" />
        <pd_script>self.query_skip=""" + str(next_skip) + """</pd_script>
    </button>
</p>
"""
        else:
            output = """
<b>No documents found.</b>
"""
        return output

    @route(view=view_db_search)
    def _view_search(self):
        if self.search_query is None:
            self.search_query = ''
        self.search_bookmark = None
        self.search_prev_bookmark=None
        return """
<div class="row form-horizontal">
    <label for="search{{prefix}}" class="control-label col-sm-2">Search:</label>
    <div class="col-sm-5">
        <input type="text" class="form-control" id="search{{prefix}}" value="{{self.search_query}}" />
    </div>
    <div class="col-sm-1">
        <button type="submit" class="btn btn-primary">Go
            <target pd_target="target2{{prefix}}" pd_options="view=""" + view_db_search_results + """" />
            <pd_script>self.search_query=$val(search{{prefix}})</pd_script>
        </button>
    </div>
</div>
<div class="row" style="margin-top: 15px;">
    <div id="target2{{prefix}}"></div>
</div>
"""

    @route(view=view_db_search_results)
    def _view_search_results(self):
        response = self.run_search(self.host, self.username, self.password, self.db,
                                   self.search_doc, self.search_index, self.search_query,
                                   self.search_limit, self.search_bookmark)
        if 'rows' in response.keys():
            output = self.format_docs(map(lambda x: x['doc'],response['rows']), view_generate_dataframe_search, 'target2')
            # previous/next buttons
            if 'bookmark' in response.keys():
                next_bookmark = response['bookmark']
            else:
                next_bookmark = None
            if self.search_bookmark is not None or next_bookmark is not None:
                output += """
<p>"""
                if self.search_bookmark is not None:
                    if self.search_prev_bookmark is None:
                        prev_bookmark_str = 'None'
                    else:
                        prev_bookmark_str = '"{}"'.format(self.search_prev_bookmark)
                    output +="""
    <button type="submit" class="btn btn-primary">Previous
        <target pd_target="target2{{prefix}}" pd_options="view=""" + view_db_search_results + """" />
        <pd_script>self.search_bookmark=""" + prev_bookmark_str + """</pd_script>
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
    <button type="submit" class="btn btn-primary">Next
        <target pd_target="target2{{prefix}}" pd_options="view=""" + view_db_search_results + """" />
        <pd_script>self.search_prev_bookmark=""" + prev_bookmark_str + """
self.search_bookmark=""" + next_bookmark_str + """</pd_script>
    </button>
</p>
"""
        else:
            output = """
<b>No documents found.</b>
"""
        return output

    @route(view=view_db_view)
    def _view_view(self):
        self.view_skip = 0
        return self._view_view_page()

    @route(view=view_db_view_page)
    def _view_view_page(self):
        response = self.get_view(self.host, self.username, self.password, self.db,
                                 self.view_doc, self.view_name, self.view_limit, self.view_skip)
        if 'rows' in response.keys():
            output = self.format_docs(map(lambda x: x['doc'], response['rows']), view_generate_dataframe_view, 'target')
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
<p>"""
                if show_prev_button:
                    output +="""
    <button type="submit" class="btn btn-primary">Previous
        <target pd_target="target{{prefix}}" pd_options="view=""" + view_db_view_page + """" />
        <pd_script>self.view_skip=""" + str(prev_skip) + """</pd_script>
    </button>"""
                if show_next_button:
                    output +="""
    <button type="submit" class="btn btn-primary">Next
        <target pd_target="target{{prefix}}" pd_options="view=""" + view_db_view_page + """" />
        <pd_script>self.view_skip=""" + str(next_skip) + """</pd_script>
    </button>
</p>
"""
        else:
            output = """
<b>No documents found.</b>
"""
        return output

    @route(view=view_generate_dataframe_all_docs)
    def _generate_dataframe_all_docs(self):
        sparkSession = SparkSession.builder.getOrCreate()
        df_reader = sparkSession.read.format("com.cloudant.spark")
        self.df = df_reader.load(self.db)
        output = 'DataFrame generated for {}/all docs. Access by calling app.get_data_frame()'.format(self.db)
        return """
<p>""" + output + """</p>
"""

    @route(view=view_generate_dataframe_query)
    def _generate_dataframe_query(self):
        response = self.run_query(self.host, self.username, self.password, self.db, self.query, -1, 0)
        if 'docs' in response.keys():
            sparkSession = SparkSession.builder.getOrCreate()
            self.df = sparkSession.createDataFrame(response['docs'])
            output = 'DataFrame generated for {}/query. Access by calling app.get_data_frame()'.format(self.db)
        else:
            output = 'No documents found.'
        return """
<p>""" + output + """</p>
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
            sparkSession = SparkSession.builder.getOrCreate()
            self.df = sparkSession.createDataFrame(docs)
            output = 'DataFrame generated for {}/search. Access by calling app.get_data_frame()'.format(self.db)
        else:
            output = 'No documents found.'
        return """
<p>""" + output + """</p>"""

    @route(view=view_generate_dataframe_view)
    def _generate_dataframe_view(self):
        sparkSession = SparkSession.builder.getOrCreate()
        self.df = sparkSession.read.format("com.cloudant.spark") \
            .option("index", "_design/{}/_view/{}".format(self.view_doc, self.view_name)) \
            .load(self.db)
        output = 'DataFrame generated for {}/{}/{}. Access by calling app.get_data_frame()' \
            .format(self.db, self.view_doc, self.view_name)
        return """
<p>""" + output + """</p>
"""

    def get_all_dbs(self, host, username, password):
        url = 'https://{}/_all_dbs'.format(host)
        r = requests.get(url, headers={
            'Authorization': 'Basic {}'.format(base64.b64encode('{}:{}'.format(username, password))),
            'Accept': 'application/json'
        })
        return r.json()

    def get_all_docs(self, host, username, password, db, limit, skip):
        url = 'https://{}/{}/_all_docs?include_docs=true'.format(host,db)
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
        url = 'https://{}/{}/_all_docs?startkey="_design/"&endkey="_design0"&include_docs=true'.format(host,db)
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
        url = 'https://{}/{}/_find'.format(host, db)
        r = requests.post(url, data=query, headers={
            'Authorization': 'Basic {}'.format(base64.b64encode('{}:{}'.format(username, password))),
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        return r.json()

    def run_search(self, host, username, password, db, design_doc, index, query, limit, bookmark):
        url = 'https://{}/{}/_design/{}/_search/{}?q={}&include_docs=true'.format(host, db, design_doc, index, query)
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
        url = 'https://{}/{}/_design/{}/_view/{}?include_docs=true'.format(host, db, design_doc, view)
        if limit > 0:
            url = '{}&limit={}'.format(url, limit)
        if skip > 0:
            url = '{}&skip={}'.format(url, skip)
        r = requests.get(url, headers={
            'Authorization': 'Basic {}'.format(base64.b64encode('{}:{}'.format(username, password))),
            'Accept': 'application/json'
        })
        return r.json()

    def format_docs(self, docs, generate_dataframe_view, generate_dataframe_target):
        output = ''
        if generate_dataframe_view is not None:
            output +="""
<p>
    <button type="submit" class="btn btn-primary">Generate DataFrame
        <target pd_target=\"""" + generate_dataframe_target + """{{prefix}}" pd_options="view=""" + generate_dataframe_view + """" />
    </button>
</p>
"""
        i = -1
        for doc in docs:
            i = i + 1
            output += '<p>'
            output += '<a href="#doc' + str(i) + '-{{prefix}}" data-toggle="collapse">' + doc['_id'] + '</a>'
            output += '<div id="doc' + str(i) + '-{{prefix}}" class="collapse">'
            output += '<pre>{}</pre>'.format(self.escape_html(json.dumps(doc, indent=2, sort_keys=True)))
            output += '</div>'
            output += '</p>'
        return output

    def escape_html(self, text):
        return escape(text)
