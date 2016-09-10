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
import mpld3.plugins as plugins
from mpld3 import utils

class ElementInfoPlugin(plugins.PluginBase):
    
    JAVASCRIPT = """
    mpld3.register_plugin("elementInfo", ElementInfoPlugin);
    ElementInfoPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    ElementInfoPlugin.prototype.constructor = ElementInfoPlugin;
    ElementInfoPlugin.prototype.requiredProps = ["id","info"];
    function ElementInfoPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };
    
    ElementInfoPlugin.prototype.draw = function(){
        var obj = mpld3.get_element(this.props.id);
        var info = this.props.info;
        if (obj ){
            obj.elements()
                .each(function(d,i){
                    d3.select(this).attr("color",this.style.fill)
                })
                .on("mouseover", function(d) {
                    d3.select(this).style("fill", "#504554").style("stroke","white")
                })                  
                .on("mouseout", function(d) {
                    d3.select(this).style("fill", d3.select(this).attr("color")).style("stroke","black")
                })
                .append("svg:title")
                .text(function(d) { return info; })
        }else{
            console.log("Unable to find element with id",this.props.id);
        }
    }
    """
    def __init__(self, element,info):
        self.dict_ = {"type": "elementInfo",
                      "id": utils.get_id(element),
                      "info":info}