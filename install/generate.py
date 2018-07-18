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

from jupyter_core.application import JupyterApp
from jinja2 import Environment, PackageLoader
from collections import OrderedDict
from six.moves import input
from six import iteritems
import os

class PixiedustGenerate(JupyterApp):
    env = Environment(loader=PackageLoader('install', 'templates'))

    def __init__(self, **kwargs):
        super(PixiedustGenerate, self).__init__(**kwargs)
        self.step = 1

    def hilite(self, message):
        return '\x1b[%sm%s\x1b[0m' % (';'.join(['32', '1']), message)

    def confirm(self, message, action="Keep"):
        answer = input(self.hilite(message) + "\n\t" + action + " y/n [y]? ")
        return 'y' if answer == '' else answer

    def input(self, message, validate=None, allowEmpty=False):
        value = None
        while value == None:
            value = input(self.hilite(message) )
            if not allowEmpty and value == "":
                value=None
            if validate is not None:
                v = validate(value)
                if not v[0]:
                    print(v[1])
                    value = None
        return value

    def start(self):
        try:
            self.files = []
            self.doStart()
        except KeyboardInterrupt:
            print("\nPixieDust generator aborted by user")

    def getStep(self):
        step = self.step
        self.step += 1
        return step

    def doStart(self):
        self.projectName = self.input(self.hilite("Step {}: Please enter the name of your project: ".format( self.getStep() )))
        self.location = os.getcwd()
        answer = self.confirm(self.hilite("Step {0}: Directory for your project: {1}".format( self.getStep(), self.location )))
        if answer != 'y':
            self.location = self.input(
                self.hilite("Please enter a directory for your project: "),
                lambda _: (os.path.exists(_), "Directory {} does not exist. Please try again or CTRL+C to abort".format(_))
            )
        
        #Check if directory already exists
        self.fullPath = os.path.join(self.location, self.projectName )
        if os.path.exists( self.fullPath ):
            print("Folder {} already exist. Exiting...".format(self.fullPath))
            return

        self.projectAuthor = self.input(self.hilite("Step {}: [Optional] Please enter the project author: ".format(self.getStep() )), allowEmpty=True)
        self.projectAuthorEmail = self.input(self.hilite("Step {}: [Optional] Please enter the project author email address: ".format(self.getStep() )), allowEmpty=True)
        self.projectUrl = self.input(self.hilite("Step {}: [Optional] Please enter the project url: ".format(self.getStep() )), allowEmpty=True)

        projectTypes = OrderedDict([
            ("1", ("Display Visualization", self.doDisplayVisualization)),
            ("2", ("Chart Renderer", self.doChartRenderer))
        ])
        print(self.hilite("Step {}: Please enter the project type:".format( self.getStep())))
        for key, value in iteritems(projectTypes):
            print("\t{0}.{1}".format(key, value[0]))
        projectType = self.input(self.hilite("Project type:"))

        if projectType not in projectTypes:
            print("Project Type {0} is not supported. Exiting...".format(projectType) )

        #Create the directory
        os.mkdir(self.fullPath)
        os.mkdir(os.path.join(self.fullPath, self.projectName))

        #Create the project artifacts
        self.writeFile(["setup.pytpl","LICENSE.tpl","MANIFEST.intpl","readme.mdtpl","setup.cfgtpl"])

        #Call out the generator function specific to the project type
        projectTypes.get(projectType)[1]()

    def writeFile(self, templates, dirName = None, targetFile=None):
        fullPath = self.fullPath if dirName is None else os.path.join(self.fullPath, dirName)
        for template in templates:
            if template.endswith("tpl"):
                if targetFile is None or len(templates) > 1:
                    targetFile = template[:-3]
                    if targetFile.endswith("."):
                        targetFile = targetFile[:-1]
                    index = targetFile.rfind('/')
                    targetFile = targetFile[index+1:] if index >= 0 else targetFile
                fullPathTargetFile = os.path.join(fullPath, targetFile)
                self.files.append(fullPathTargetFile)
                with open( fullPathTargetFile, "wb" ) as f:
                    f.write(PixiedustGenerate.env.get_template(template).render(this=self).encode("utf-8","ignore"))


    def doDisplayVisualization(self):
        print("Generating Display Visualization bootstrap code...")
        self.displayClassName = self.input(self.hilite(
            "Step {0}. Please enter the Display Handler class name. e.g {1}Handler: ".format(self.getStep(), self.projectName.capitalize())
        ))
        self.writeFile(["display/__init__.pytpl", "display/display.pytpl"], dirName=self.projectName)

        templateDir = os.path.join(self.fullPath,self.projectName,"templates")
        os.mkdir(templateDir)
        self.writeFile(["display/helloWorld.htmltpl"], dirName=templateDir)

        self.displaySuccess()

    def doChartRenderer(self):
        print("Generating Chart Renderer bootstrap code")
        self.rendererClassName = self.input(self.hilite(
            "Step {0}. Please enter the prefix for renderer class name. e.g {1}: ".format(self.getStep(), self.projectName.capitalize())
        ))

        chartIds = [("barChart","bar"),("lineChart","line"),("scatterPlot","scatter"),
            ("pieChart","pie"),("mapView",None),("histogram","hist")]
        self.chartIds = self.input(self.hilite(
            "Step {0}. Please enter one or more chart id (comma separated) to be associated with this renderer. e.g {1}. Leave empty to add all: ".format(self.getStep(), [c[0] for c in chartIds] )
        ),allowEmpty=True)

        if self.chartIds == "":
            self.chartIds = [c[0] for c in chartIds]
        else:
            self.chartIds = self.chartIds.split(",")

        #write the init and base
        self.writeFile(["chart/__init__.pytpl", "chart/rendererBaseDisplay.pytpl"], dirName=self.projectName)

        for c in self.chartIds:
            self.chartId = c
            knownCharts = [x for x in chartIds if x[0]==c]
            self.plotKind = "line" if len(knownCharts)==0 or knownCharts[0][1] is None else knownCharts[0][1]
            self.writeFile(["chart/rendererDisplay.pytpl"], dirName=self.projectName, targetFile="{0}Display.py".format(c))

        self.displaySuccess()

    def displaySuccess(self):
        print("Successfully generated boostrap code with following files:")
        for f in self.files:
            print("\t{}".format(f))
