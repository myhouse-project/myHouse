$(document).ready(function(){
	
	// variables
	var refresh_seconds = 5*60;
	var max_forecast_entries = 6;

	// helper to replace all occurences in a string
	String.prototype.replaceAll = function (find, replace) {
		var str = this;
		return str.replace(new RegExp(find.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'), 'g'), replace);
	};

	// return an empty HTML widget template
	function get_widget_template(group_id,type,title,size) {
		// define the widget HTML
		var html = '\
					<div class="col-md-#size#">\
							<div class="box box-solid box-primary">\
								<div class="box-header">\
									<h3 class="box-title">#title#</h3>\
								</div>\
								<div class="box-body no-padding box-primary">\
								    <div class="box-body" id="#group_id#_#type#">\
									</div>\
								</div>\
							</div>\
					</div>\
				';		
		// replace the placeholders with the provided input
		html = html.replaceAll("#size#",size);
		html = html.replaceAll("#title#",title);
		html = html.replaceAll("#type#",type);
		html = html.replaceAll("#group_id#",group_id);
		return html;
	}
	
	// return an sensor summary HTML body
	function get_summary_body(group_id) {
		// define the widget HTML
		var html = '\
									<div class="box-profile">\
										<img class="profile-user-img img-responsive img-circle" id="#group_id#_icon" src="web/images/unknown.png">\
										<h3 class="profile-username text-center"><span id="#group_id#_current">Loading...</span><span id="#group_id#_current_suffix"></span></h3>\
										<p class="text-muted text-center" id="#group_id#_timestamp">...</p>\
											<ul class="list-group list-group-unbordered">\
												<li class="list-group-item" id="#group_id#_summary_chart">\
												</li>\
											</ul>\
									<div>\
											';
		// replace the placeholders with the provided input
		html = html.replaceAll("#group_id#",group_id);
		return html;
	}
	
	// set the html of a given tag
	function set_html(tag,url) {
		$.getJSON(url, function(tag) {
				return function (data) {
					if (data.length != 1) $(tag).html("N/A");
					$(tag).html(data[0]);
				};
		}(tag));
	}
	
	// set an image src
	function set_img(tag,url) {
		$.getJSON(url, function(tag) {
				return function (data) {
					if (data.length != 1) return;
					$(tag).attr('src','web/images/'+data[0]+'.png');
				};
		}(tag));
	}
	
	// add a new series to a chart
	function add_series(chart,url,sensor,series_name) {
		$.getJSON(url, function(chart,sensor,series_name) {
				return function (data) {
					// get the series template
					var series = $.extend(true,{}, sensor['timeline_series'][series_name]);
					series['name'] = sensor['display_name']+" "+series_name;
					series['id'] = sensor['sensor_id']+":"+series_name;
					// add the sensor suffix
					if (!('tooltip' in sensor)) series['tooltip'] = {};
					if ('value_suffix' in sensor) series['tooltip']['valueSuffix'] = sensor['value_suffix'];
					//add the data to it and attach to the chart
					series['data'] = data;
					// if the data is a string, add flags
					if (sensor['format'] == 'string') {
						flags = [];
						for (i = 0; i < data.length; i++) {
							flags[i] = {'x': data[i][0], 'shape': 'circlepin', 'title': '<img width="20" heigth="20" src="web/images/'+data[i][1]+'.png">'};
						}
						series['data'] = flags;
					} 
					chart.addSeries(series);
				};
		}(chart,sensor,series_name));
	}
	
	// add a new point to an existing series
	function add_point(chart,url,series_index) {
		$.getJSON(url, function(chart,series_index) {
				return function (data) {
					// add the data as a new point to an existing series
					chart.series[series_index].addPoint(data);
				};
		}(chart,series_index));
	}


	function load() {
		var module = "weather"
		
		// request the configuration first
		$.getJSON("config",function(data) {
			conf = data
			// for each group
			for (var group_id in conf["modules"][module]["sensor_groups"]) {
				group = conf["modules"][module]["sensor_groups"][group_id];
				// do not render the builtin group
				if (group_id == "__builtin__") continue;
				// define the tags to use
				var row1 = group_id+"_row1";
				var row2 = group_id+"_row2";
				var summary_widget = "#"+group_id+"_summary";
				var summary_current = "#"+group_id+"_current";
				var summary_current_suffix = "#"+group_id+"_current_suffix";
				var summary_timestamp = "#"+group_id+"_timestamp";
				var summary_icon = "#"+group_id+"_icon";
				var summary_chart = "#"+group_id+"_summary_chart";
				// start a new row
				$("#sensors").append('<div class="row" id="'+row1+'">');
				
				// SUMMARY WIDGET
				// add a new empty widget
				$("#"+row1).append(get_widget_template(group_id,"summary",group["display_name"]+": summary",3));
				// add the summary body to it
				$(summary_widget).html(get_summary_body(group_id));
				// add the summary chart
				var options = $.extend(true,{}, conf["charts"]["summary"]);
				$(summary_chart).highcharts(options);
				var chart = $(summary_chart).highcharts();

				// add the summary icon
				var icon_sensor = group['summary_icon'].match(/sensor:\/\/(.+)$/);
				if (icon_sensor) set_img(summary_icon,module+"/sensors/"+icon_sensor[1])
				var icon_file = group['summary_icon'].match(/file:\/\/(.+)$/);
				if (icon_file) $(summary_icon).attr('src','web/images/'+icon_file[1]);
				
				// for each sensor
				for (var sensor_id in group["sensors"]) {
					var sensor = group["sensors"][sensor_id];
					sensor['sensor_id']= sensor_id;
					var sensor_url = module+"/sensors/"+group_id+"/"+sensor_id;
					// skip flags
					if (sensor['format'] == 'string') continue;
					// if the sensor has to be shown in the summary add the current measure and timestamp
					if (sensor_id == group['summary_sensor']) {
						set_html(summary_current,sensor_url+"/current");
						if ('value_suffix' in sensor) $(summary_current_suffix).html(sensor['value_suffix']);
						set_html(summary_timestamp,sensor_url+"/timestamp");
					}
					// add the sensor to the xAxis
					chart['xAxis'][0]['categories'].push(sensor["display_name"]);
					// add the point for yesterday's range
					add_point(chart,sensor_url+"/yesterday/range",0);
					// add the point for today's range
					add_point(chart,sensor_url+"/today/range",1);
				}
				
				// RECENT/HISTORY CHARTS
				var timeline_charts = {'recent': 3, 'history':6,}
				// for each timeline chart
				for (chart_type in timeline_charts) {
					// append a new empty widget
					$("#"+row1).append(get_widget_template(group_id,chart_type,group["display_name"]+": "+chart_type,timeline_charts[chart_type]));
					// set chart options
					var options = $.extend(true,{}, conf["charts"][chart_type]);
					// create the chart
					var timeline_chart = "#"+group_id+"_"+chart_type;
					$(timeline_chart).highcharts('StockChart',options);
					var chart = $(timeline_chart).highcharts();
					// for each sensor
					for (var sensor_id in group["sensors"]) {
						var sensor = group["sensors"][sensor_id];
						sensor['sensor_id']= sensor_id;
						var sensor_url = module+"/sensors/"+group_id+"/"+sensor_id;
						// add a new line to the chart for each series
						for (var series_name in sensor["timeline_series"]) {
							//add_series(chart,sensor_url+"/"+chart_type+"/"+series_name,sensor,series_name);
						}
					}
				}
				// end of the row
				$("#"+row1).append('</div>');
			} // end for each group
			
        });
	}
	
	// load the page
	load();
	
	// refresh the page
	setInterval(function(){
		$("#sensors").empty();
		load();
	}, refresh_seconds*1000);

	
	
});
