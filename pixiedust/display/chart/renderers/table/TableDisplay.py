from pixiedust.display.chart.renderers import PixiedustRenderer
from .TableBaseDisplay import TableBaseDisplay
from pixiedust.utils import cache
from pixiedust.utils import Logger

@PixiedustRenderer(id="tableView")
@Logger()
class TableDisplay(TableBaseDisplay):

    def doRenderChart(self):
        wpdf = self.getWorkingPandasDataFrame()
        table_showrows = self.options.get("table_showrows", 'All')
        if table_showrows == 'Missing values':
            wpdf = wpdf[wpdf.isna().any(axis=1) if hasattr(wpdf,'isna') else wpdf.isnull().any(axis=1)]
        elif table_showrows == 'Not missing values':
            wpdf = wpdf[wpdf.notna().all(axis=1) if hasattr(wpdf,'notna') else wpdf.notnull().all(axis=1)]


        return self.renderTemplate("table.html", wpdf=wpdf,
            table_noschema=self.options.get("table_noschema", "false"),
            table_nocount=self.options.get("table_nocount", "false"),
            table_nosearch=self.options.get("table_nosearch", "false"))
