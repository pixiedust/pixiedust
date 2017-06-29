'''
-------------------------------------------------------------------------------

Copyright IBM Corp. 2017

Licensed under the Apache License, Version 2.0 (the 'License');

you may not use this file except in compliance with the License.

You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software

distributed under the License is distributed on an 'AS IS' BASIS,

WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

See the License for the specific language governing permissions and

limitations under the License.

-------------------------------------------------------------------------------
'''

# MongoDB Browser for PixieDust
# Author: Nick Kasten
# Summer 2017

import ssl
import re
import pandas as pd
from pixiedust.display.app import *
try:
    import pymongo
    from bson.json_util import dumps
    display_dependency_instructions = False
except NameError:
    display_dependency_instructions = True

@PixieApp
class mongo_db_browser:
    #-------------------------- UTILITY METHODS --------------------------#
    def create_client(self, flag=None):
        try:
            client = pymongo.MongoClient(self.mongo_uri + "&ssl_cert_reqs=CERT_NONE")
        except pymongo.errors.PyMongoError:
            client = None
            self.exception("Error connecting to Mongo DB.")
        return client
        
    def get_docs(self, start=0, end=None):
        return list(self.client[self.db][self.collection].find()[start:end])

    def format_raw_query(self):
        split_query = [x.lstrip() for x in re.sub(r'(?:&quot;)|(?:&apos;)', '"', self.raw_query).split('\n') if len(x) > 6 and len(x.strip()) != 0]
        formatted_sort_list = []
        for item in eval(split_query[2][8:]):
            formatted_sort_list += [(key, self.convert_dir(val)) for (key, val) in item.items()]
        return [eval(split_query[0][12:-1]), eval(split_query[1][14:-1]), formatted_sort_list]

    def get_query_docs(self, start=0, end=None):
        return list(self.client[self.db][self.collection].find(self.formatted_query[0], self.formatted_query[1])[start:end])

    def convert_dir(self, dir_string):
        if dir_string == 'ascending' or dir_string == 'asc':
            return 1
        elif dir_string == 'descending' or dir_string == 'desc':
            return -1

    def get_dataframe(self):
        return self.output_dataframe

    def go_back(self):
        if int(self.doc_index) >= self.page_size:
            return self.doc_index-self.page_size
        else:
            return self.doc_index
            
    def go_fwd(self):
        if int(self.doc_index) <= self.doc_count-self.page_size:
            return self.doc_index+self.page_size
        else:
            return self.doc_index
    #-------------------------- DYNAMIC CONTENT METHODS --------------------------#
    def create_list_head(self, item_type):
        if item_type == "db":
            title = """Select a DB to see a list of its collections:"""
        elif item_type == "collection":
            title = """Select a Collection to see available documents:"""
        return """
        <style>
            #button_list {
                list-style: none;
                padding: 0;
                margin: 0;
            }
            i {
                margin-right: 10px;
            }
            li {
                margin-bottom: 10px;
            }
        </style>
        <link href="https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css" rel="stylesheet" integrity="sha384-wvfXpqpZZVQGK6TAh5PVlGOfQNHSoD2xbE+QkPxCAFlNEevoEH3Sl0sibVcOQVnN" crossorigin="anonymous">
        <div class="row text-center">
            <div class="jumbotron">
                <h2>""" + title + """</h2>
            </div>"""

    def create_button_list(self, item_type, button_names):
        if item_type == "db":
            icon_name = "fa-database"
            script = """'self.db="{0}"'"""
            view = "collection_list"
        elif item_type == "collection":
            icon_name = "fa-files-o"
            script = """'self.collection="{0}"'"""
            view = "doc_preview"

        button_list = """<ul id="button_list">"""
        for name in button_names:
            button_list += """
            <li>
                <button 
                    id=""" + name + """
                    class="btn btn-primary"
                    pd_script=""" + script.format(name) + """
                    pd_options="view=""" + view +"""">
                    <i class="fa """ + icon_name + """" aria-hidden="true"></i> 
                    """ + name + """
                </button>
            </li>"""
        button_list += """
            <li>
                <button 
                    pd_options="view="
                    class="btn btn-default">Back
                </button>
            </li>
        </ul>"""
        return button_list

    def create_side_navbar(self):
        return """
        <div id="coll_controls" class="col-sm-2">
            <button 
                style="margin-bottom: 10px;"
                pd_options="view=collection_list"
                class="btn btn-default">Back
            </button>
            <h3>{{this.collection}}</h3>
            <button 
                style="margin-top: 10px;"
                pd_options="view=doc_viewer"
                pd_script="self.all_docs=self.get_docs()\nself.doc_index=0\nself.all_doc_view='true'\nself.dataframe_generated='false'"
                class="btn btn-primary">View All Documents
            </button>
            <button 
                style="margin-top: 10px;"
                pd_options="view=create_query"
                pd_script="self.all_doc_view='false'\nself.dataframe_generated='false'"
                class="btn btn-primary">Query Documents
            </button>
        </div>"""

    def create_doc_viewer_head(self):
        return """
        <style>
            #doc_container {
                padding: 0px 10px 0px 30px;
            }
            #coll_controls {
                padding: 10px;
            }
            #outer_row {
                margin: 10px;
                border: 1px solid #ddd;
                border-radius: 4px 4px 0px 0px;
            }  
            #viewer_heading {
                padding: 0px 0px 10px 10px;
            }
            #mid_row {
                padding: 15px;
                margin-bottom: 0px;
                background-color: #f5f5f5;
            }
            #doc_navbar {
                margin-top: 10px;
            }
            
            #doc_navbar span {
                padding-left: 5px;
            }
            textarea {
                margin-bottom: 15px; 
                padding: 10px; 
                font-family: monospace;
                font-size: 9pt; 
                background-color: white; 
                max-height: 200px; 
                white-space: pre; 
                overflow: scroll; 
                border-style: solid; 
                border-radius: 2px; 
                border-width: 1px; 
                border-color: #aaa;
            }
            .hiddenWell {
                margin: 0px 20px 0px 20px; 
                padding: 10px; 
                font-family: monospace;
                font-size: 9pt; 
                background-color: white; 
                max-height: 200px; 
                white-space: pre; 
                overflow: scroll; 
                border-style: solid; 
                border-radius: 2px; 
                border-width: 1px; 
                border-color: #aaa;
            }            
            .doc_element {
                margin-top: 10px;
                font-size: 9pt;
            }
            .doc_element a {
                text-decoration: none !important;
            }
        </style>"""

    def create_doc_viewer(self):
        page_title = 'All Documents' if self.all_doc_view == 'true' else 'Query Results'
        list_head = """<div class="row">""" + self.create_side_navbar() + """ 
            <div id="doc_container" class="col-sm-10">
                <div id="outer_row" class="row">
                    <h4 id="viewer_heading">""" + page_title + """</h4>
                    <div id="mid_row" class="row">
                        <div id="inner_row" class="row">
                            <div id="doc_target{{prefix}}">"""
        current_page_range = [x for x in self.all_docs[self.doc_index: self.doc_index+self.page_size]]
        doc_list = self.create_doc_elements(current_page_range)
        list_tail = self.create_doc_navbar() + """
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>"""
        return list_head + doc_list + list_tail

    def create_doc_navbar(self):
        output = """
        <div id="doc_navbar">
            {% if this.doc_index >= this.page_size %}
                <button 
                    pd_options="view=doc_viewer" 
                    pd_script="self.doc_index=self.go_back()" 
                    type="button" 
                    class="btn btn-primary btn-sm control_btn">Prev
                </button>
            {% endif %}
            {% if this.doc_index <= this.doc_count - this.page_size %}
                <button 
                    pd_options="view=doc_viewer" 
                    pd_script="self.doc_index=self.go_fwd()" 
                    type="button" 
                    class="btn btn-primary btn-sm control_btn">Next
                </button>
            {% endif %}"""
        output += """
            <span><b>{0} to {1} of {2}</b></span>
            <hr style="border: 1px solid #ddd;">""".format(self.doc_index+1, self.doc_index+self.page_size, self.doc_count)
        output += """<h4>Access dataframe with .get_dataframe() method.</h4>""" if self.dataframe_generated == 'true' else """
            <button 
                pd_options="view=doc_viewer"
                pd_script="self.output_dataframe=pd.DataFrame(self.all_docs)\nself.dataframe_generated='true'" 
                type="button" 
                class="btn btn-info btn control_btn">Generate Dataframe
            </button>
        </div>"""
        return output

    def create_doc_elements(self, doc_list):
        output = ""
        count = 0
        for doc in doc_list:
            count += 1
            doc_dict = [[x, y] for (x, y) in zip(doc.keys(), doc.values())]
            preview_lines = 4 if (len(doc_dict) >= 4) else len(doc_dict)
            output += """
            <div class="doc_element">
                <a href="#doc""" + str(count) + """-{{prefix}}" data-toggle="collapse"> """ + """<pre> {0} {{</pre>""".format(doc['_id'])
            for i in list(range(1, preview_lines)):
                if len(str(doc_dict[i][1])) > 20:
                    doc_dict[i][1] = str(doc_dict[i][1])[0:20] + '...'
                output += """<pre>  "{0}": {1}</pre>""".format(doc_dict[i][0], doc_dict[i][1])
            output += """<pre>  ...</pre></a>
                <div id="doc""" + str(count) + """-{{prefix}}" class="collapse hiddenWell">""" + dumps(doc, indent=2, sort_keys="true") + """
                </div><a href="#doc""" + str(count) + """-{{prefix}}" data-toggle="collapse">""" +  """<pre>}</pre></a>
            </div>"""
        return output
    #-------------------------- ROUTES/VIEWS --------------------------#
    @route()
    def default_route(self):
        self.mongo_uri = ""
        self.page_size = 5

        if display_dependency_instructions == True:
            output = """<div class="row text-center" style="font-size: 12pt;">Please install <b>pymongo</b> by running the following command: <code>!pip install pymongo</code></div>"""
        else:
            output = """
        <div class="row">
            <h3>Enter your MongoDB URI to list available DBs:</h3>
        </div>
        <div class="row">
            <div class="form-group">
                <input 
                    id="mongo_uri"
                    type="text" 
                    class="form-control" 
                    rows="1" 
                />
                <button 
                    type="submit" 
                    style="margin-top: 5px;"
                    pd_options="view=db_list"
                    pd_script="self.mongo_uri='$val(mongo_uri)'" 
                    class="btn btn-success">Connect
                </button>
            </div>
        </div>"""
        return output

    @route(view="db_list")
    def db_list(self):
        self.client = self.create_client('no_ssl_cert')
        return self.create_list_head("db") + self.create_button_list("db", self.client.database_names()) + """</div>"""

    @route(view="collection_list")
    def collection_list(self):
        return self.create_list_head("collection") + self.create_button_list("collection", self.client[self.db].collection_names()) + """</div>"""

    @route(view='doc_preview')
    def doc_preview(self):
        return """<div class="row">""" + self.create_side_navbar() + """</div>"""

    @route(view='doc_viewer')
    def doc_viewer(self):
        self.doc_count = len(self.all_docs)
        return self.create_doc_viewer_head() + self.create_doc_viewer()

    @route(view='create_query')
    def create_query(self):
        self.query = """
{
    "selector": {"_id": {"$exists": "true"}},
    "projection": ["_id"],
    "sort": [{"_id": "ascending"}]
}"""
        return self.create_doc_viewer_head() + """
        <div class="row"> """ + self.create_side_navbar() + """
            <div id="doc_container" class="col-sm-10">
                    <div id="outer_row" class="row">
                        <h4 id="viewer_heading">Query</h4>
                        <div id="mid_row" class="row">
                            <div id="inner_row" class="row">
                                <div class="form-group">
                                    <textarea rows="6" class="form-control" id="query{{prefix}}">""" + self.query + """
                                    </textarea>  
                                    <button 
                                        type="submit"
                                        pd_options="view=doc_viewer"
                                        pd_script='self.raw_query="$val(query{{prefix}})"\nself.formatted_query=self.format_raw_query()\nself.doc_index=0\nself.all_docs=self.get_query_docs()'
                                        class="btn ">Go
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>"""