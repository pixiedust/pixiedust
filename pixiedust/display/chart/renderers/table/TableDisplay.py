from pixiedust.display.chart.renderers import PixiedustRenderer
from .TableBaseDisplay import TableBaseDisplay
from pixiedust.utils import cache
from pixiedust.utils import Logger

@PixiedustRenderer(id="tableView")
@Logger()
class TableDisplay(TableBaseDisplay):

    def doRenderChart(self):
        wpdf = self.getWorkingPandasDataFrame()
        table_onlymissing = self.options.get("table_onlymissing", False)
        if str(table_onlymissing).lower() == 'true':
            wpdf = wpdf[wpdf.isnull().any(axis=1)]

        return self.renderTemplate("table.html", wpdf=wpdf,
            table_noschema=self.options.get("table_noschema", "false"),
            table_nocount=self.options.get("table_nocount", "false"),
            table_nosearch=self.options.get("table_nosearch", "false"))
