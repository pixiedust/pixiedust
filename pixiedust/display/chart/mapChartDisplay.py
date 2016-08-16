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

from .display import ChartDisplay
    
class MapChartDisplay(ChartDisplay):
    pass

    def GeoChart(data_string, element):
        return Javascript("""
            //container.show();
            function draw() {{
            var chart = new google.visualization.GeoChart(document.getElementById(""" + element + """));
            chart.draw(google.visualization.arrayToDataTable(""" + data_string + """));
            }}
            google.load('visualization', '1.0', {'callback': draw, 'packages':['geochart']});
            """, lib="https://www.google.com/jsapi")