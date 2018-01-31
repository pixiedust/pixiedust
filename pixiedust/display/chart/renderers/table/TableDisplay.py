from pixiedust.display.chart.renderers import PixiedustRenderer
from .TableBaseDisplay import TableBaseDisplay
from pixiedust.utils import cache
from pixiedust.utils import Logger

@PixiedustRenderer(id="tableView")
@Logger()
class TableDisplay(TableBaseDisplay):

    def doRenderChart(self):
        return self.renderTemplate("table.html", wpdf=self.getWorkingPandasDataFrame())
