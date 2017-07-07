function draw() {
	var drawOptions = {
		region: '{{this.options.get("mapRegion")}}',
		displayMode: '{{this.options.get("mapDisplayMode")}}',
		resolution: '{{this.options.get("mapResolution")}}',
		colorAxis: {colors: JSON.parse('{{this.options.get("mapColorAxis")}}')},
		sizeAxis: {minSize: 6, maxSize: 15}
	};

	var chart = new google.visualization.GeoChart(document.getElementById('map-{{prefix}}-{{randomid}}'));
	var data = google.visualization.arrayToDataTable({{this.options.get("mapData")}});

	google.visualization.events.addListener(chart, 'select', function(){
		try{
			var sel = chart.getSelection();
			for (var i = 0; i < sel.length; i++) {
				var item = sel[i];
				var d = data;
				if ( item.row ){
					var payload = {type:"select", targetDivId: "{{this.options.get("targetDivId","") }}" };
					for (var j = 0; j < d.getNumberOfColumns(); j++ ){
						payload[d.getColumnLabel(j)] = d.getFormattedValue(item.row,j);
					}
					$(document).trigger('pd_event', payload);
				}
			}
		}catch(e){
			console.log("Unexcepted exception",e);
		}
	});

	chart.draw(data, drawOptions);
}

google.load('visualization', '1.0', {'callback': draw, 'packages':['geochart']});