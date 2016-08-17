$("#mapOptions{{prefix}}").click(function(){
    {%include module + ":chartOptions.dialog" %}
});
function draw() {
	var drawOptions = {
		region: '{{this.options.get("mapRegion")}}',
        displayMode: '{{this.options.get("mapDisplayMode")}}'
	};
	var chart = new google.visualization.GeoChart(document.getElementById('map{{prefix}}'));
	chart.draw(google.visualization.arrayToDataTable({{this.options.get("mapData")}}), drawOptions);
}
google.load('visualization', '1.0', {'callback': draw, 'packages':['geochart']});