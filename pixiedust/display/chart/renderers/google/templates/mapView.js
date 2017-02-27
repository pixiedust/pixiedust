function draw() {
	var drawOptions = {
		region: '{{this.options.get("mapRegion")}}',
		displayMode: '{{this.options.get("mapDisplayMode")}}',
		resolution: '{{this.options.get("mapResolution")}}'
	};

	var chart = new google.visualization.GeoChart(document.getElementById('map{{prefix}}'));
	var data = google.visualization.arrayToDataTable({{this.options.get("mapData")}});

	chart.draw(data, drawOptions);
}

google.load('visualization', '1.0', {'callback': draw, 'packages':['geochart']});