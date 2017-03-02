function draw() {
	var drawOptions = {
		region: '{{this.options.get("mapRegion")}}',
		displayMode: '{{this.options.get("mapDisplayMode")}}',
		resolution: '{{this.options.get("mapResolution")}}',
		colorAxis: {colors: ['#FF007F', '#007FFF', '#7FFF00']},
		sizeAxis: {minSize: 6, maxSize: 15}
	};

	var chart = new google.visualization.GeoChart(document.getElementById('map{{prefix}}'));
	var data = google.visualization.arrayToDataTable({{this.options.get("mapData")}});

	chart.draw(data, drawOptions);
}

google.load('visualization', '1.0', {'callback': draw, 'packages':['geochart']});