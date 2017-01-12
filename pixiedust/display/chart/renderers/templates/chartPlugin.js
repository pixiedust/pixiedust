// don't remove this comment
mpld3.register_plugin("chart", ChartPlugin);
ChartPlugin.prototype = Object.create(mpld3.Plugin.prototype);
ChartPlugin.prototype.constructor = ChartPlugin;
ChartPlugin.prototype.requiredProps = ["labels"];
function ChartPlugin(fig, props){
	mpld3.Plugin.call(this, fig, props);
};
ChartPlugin.prototype.draw = function(){
	try{
		// FIXME: this is a very brittle way to select the x-axis element
		var ax = this.fig.axes[0].elements[0];

		// getting the labels for xticks
		var labels =  this.props.labels;
		console.info("labels: "+labels);
		
		// see https://github.com/mbostock/d3/wiki/Formatting#d3_format
		// for d3js formating documentation
		ax.axis.tickFormat(function(d){
			try{
				return labels[Math.floor(d)];
			}catch(e){
				console.log(e)
			}
		});
		ax.axis.ticks(labels.length);

		// HACK: use reset to redraw figure
		this.fig.reset(); 
	}catch(e){
		console.log(e);
	}
}