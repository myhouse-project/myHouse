$(document).ready(function(){
	
	// variables
	var refresh_seconds = 5*60;
	var timezone_offset = 2;
	var max_forecast_entries = 6;
	var default_color = "#7cb5ec";

	// constants
	var hour = 3600*1000;
	var day = 24*hour;
	var columnrange_data = {};
	Highcharts.setOptions({global: {timezoneOffset: -timezone_offset * 60}});
	Highcharts.getOptions().colors[1] = Highcharts.getOptions().colors[6];
	
	String.prototype.replaceAll = function (find, replace) {
		var str = this;
		return str.replace(new RegExp(find.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'), 'g'), replace);
	};

	
	function get_widget_template(size,title,body) {
		// define the widget HTML
		var html = '\
					<div class="col-md-#size#">\
							<div class="box box-solid box-primary">\
								<div class="box-header">\
									<h3 class="box-title">#title#</h3>\
									<div class="box-tools pull-right">\
										<button class="btn btn-box-tool" data-widget="collapse">\
											<i class="fa fa-minus"></i>\
										</button>\
									</div>\
								</div>\
								<div class="box-body no-padding box-primary">\
								    <div class="box-body">\
									#body#\
									</div>\
								</div>\
							</div>\
					</div>\
				';		
		// replace the placeholders with the provided input
		html = html.replaceAll("#size#",size);
		html = html.replaceAll("#title#",title);
		html = html.replaceAll("#body#",body);
		return html;
	}
	
	function get_summary_widget(group_id,table) {
		// define the widget HTML
		var html = '\
								          <div class="box-profile">\
												<img class="profile-user-img img-responsive img-circle" id="#group_id#_summary_icon" src="web/weather-icons/unknown.png" >\
													<h3 class="profile-username text-center" id="#group_id#_summary_current">Loading...</h3>\
													<p class="text-muted text-center" id="#group_id#_summary_timestamp">...</p>\
													 <table class="table table-condensed">\
														<tbody>\
														<tr>\
															<th>Sensor</th>\
															<th>Current</th>\
															<th>Today</th>\
															<th>Yesterday</th>\
														</tr>\
														#table#\
														</tbody>\
													</table>\
											</div>';
		// replace the placeholders with the provided input
		html = html.replaceAll("#group_id#",group_id);
		html = html.replaceAll("#table#",table);
		return html;
	}
	
	function get_summary_table(group_id,sensor_id,sensor_name) {
		var html = '\
					<tr>\
						<td>#sensor_name#</td>\
						<td><span id="#group_id#_#sensor_id#_latest">...</span></td>\
						<td><span id="#group_id#_#sensor_id#_today_min">...</span> - <span id="#group_id#_#sensor_id#_today_avg">...</span> - <span id="#group_id#_#sensor_id#_today_max">...</span></td>\
						<td><span id="#group_id#_#sensor_id#_yesterday_min">...</span> - <span id="#group_id#_#sensor_id#_yesterday_avg">...</span> - <span id="#group_id#_#sensor_id#_yesterday_max">...</span></td>\
					</tr>\
					';
		html = html.replaceAll("#group_id#",group_id);
		html = html.replaceAll("#sensor_id#",sensor_id);
		html = html.replaceAll("#sensor_name#",sensor_name);
		return html;
	}
	
	function get(url,tag) {
		$.getJSON(url, function(tag) {
				return function (data) {
					$(tag).html(data[0]);
				};
		}(tag));
	}


	function load_test() {
		var module = "weather"
		
		// request the configuration		
		$.getJSON("get_config",function(data) {
			conf = data
			// for each group
			for (var group_id in conf["modules"][module]["sensor_groups"]) {
				group = conf["modules"][module]["sensor_groups"][group_id];
				// do not render the builin group
				if (group_id == "__builtin__") continue;
				var html = '<div class="row">';
				// for each sensor
				var html_table = "";
				for (var sensor_id in group["sensors"]) {
					var sensor = group["sensors"][sensor_id];
					html_table = html_table + get_summary_table(group_id,sensor_id,sensor["name"]);
				} // end for each sensor
				html_summary = get_summary_widget(group_id,html_table);
				var html_widget = get_widget_template(4,group["name"]+" Summary",html_summary);
				html = html + html_widget;
				html = html + '</div>';
				$("#sensors").append(html);
				
				for (var sensor_id in group["sensors"]) {
					get("sensors/"+module+"/"+group_id+"/"+sensor_id,"#"+group_id+"_"+sensor_id+"_latest")
					get("sensors/"+module+"/"+group_id+"/"+sensor_id+"/today/min","#"+group_id+"_"+sensor_id+"_today_min")
					get("sensors/"+module+"/"+group_id+"/"+sensor_id+"/today/avg","#"+group_id+"_"+sensor_id+"_today_avg")
					get("sensors/"+module+"/"+group_id+"/"+sensor_id+"/today/max","#"+group_id+"_"+sensor_id+"_today_max")
					get("sensors/"+module+"/"+group_id+"/"+sensor_id+"/yesterday/min","#"+group_id+"_"+sensor_id+"_yesterday_min")
					get("sensors/"+module+"/"+group_id+"/"+sensor_id+"/yesterday/avg","#"+group_id+"_"+sensor_id+"_yesterday_avg")
					get("sensors/"+module+"/"+group_id+"/"+sensor_id+"/yesterday/max","#"+group_id+"_"+sensor_id+"_yesterday_max")
				} // end for each sensor
				
			} // end for each ground
			
        });
	}

	
	/*
	
				var x = ['today','yesterday']
				
				var chart_options = $.extend(true,{}, conf["charts"]["default"]);
				chart_options['tooltip']['enabled'] = false;
				chart_options['chart']['height'] = 200;
				chart_options['chart']['inverted'] = true;
				chart_options['xAxis']['categories'] = x;
				$("#"+sensor_id+"_summary").highcharts(chart_options);
				
				var summary_chart = $("#"+sensor_id+"_summary").highcharts();*/
	
	// default chart options
	var default_chart_options = {
        'chart': {},
        'title': {'text': ''},
        'yAxis': {'title': {'text': ' '}},
		'xAxis': {},
		'credits': { 'enabled': false},
		'tooltip': {'crosshairs': true,'shared': true,'valueSuffix': '°C'},
        'legend': {'enabled': false},
		'rangeSelector' : {'selected' : 0},
    };
	
	var default_columnrange_options = {
		'type': 'columnrange',
		'colorByPoint': true, 
		'pointWidth': 10, 
		'pointPadding': 0, 
		'dataLabels': {'enabled': true, 'style': { 'fontSize': '14px'}}
	};

	var default_spline_options = {
		'type' : 'spline', 
		'lineWidth': 3,
		'zIndex' : 1,
		'marker': { 'enabled': true, 'radius': 4, 'fillColor': 'white', 'lineWidth': 2,'lineColor': default_color },
		'dataLabels': {'enabled': true, 'y': 40, 'borderRadius': 5, 'backgroundColor': 'rgba(252, 255, 197, 0.7)', 'borderWidth': 1, 'borderColor': '#AAA'},
		'enableMouseTracking': true,
	};
	
	var default_arearange_options =  {
		'type' : 'arearange', 
		'zIndex' : 0, 
		'color': default_color,
		'fillOpacity': 0.2,
		'lineWidth': 1,
		'linkedTo': ':previous'
	};
	
	var default_flags_options =  {
		'type' : 'flags', 
		'useHTML' : true, 
		'name': 'Weather',
		'onSeries': 'main',
	};
	
	// calculate the time elapsed since the given date
	function timeSince(date) {
		var seconds = Math.floor((new Date() - date) / 1000);
		var interval = Math.floor(seconds / 31536000);
		if (interval > 1) return interval + " years ago";
		interval = Math.floor(seconds / 2592000);
		if (interval > 1) return interval + " months ago";
		interval = Math.floor(seconds / 86400);
		if (interval > 1) return interval + " days ago";
		interval = Math.floor(seconds / 3600);
		if (interval > 1) return interval + " hours ago";
		interval = Math.floor(seconds / 60);
		if (interval > 1) return interval + " minutes ago";
		return Math.floor(seconds) + " seconds ago";
	}
	
	// load the webcams
	function load_webcams() {
		$.getJSON("weather/static/webcams",function(data) {
			for (var i in data) {
				var webcam_num = parseInt(i)+1;
				$("#webcam_"+webcam_num).attr("src",data[i]["url"]);
			}
		});
	}
	
	// load the forecast
	function load_forecast() {
		$.getJSON("weather/forecast",function(data) {
			$("#forecast").empty();
			for (i in data["forecast"]["simpleforecast"]["forecastday"]) {
				entry = data["forecast"]["simpleforecast"]["forecastday"][i];
				var title = entry["date"]["weekday"]+', '+entry["date"]["monthname"]+' '+entry["date"]["day"]+' '+entry["date"]["year"];
				var description = entry["conditions"]+'. ';
				if (entry["pop"] > 0) description = description + 'Precip. '+entry["pop"]+'%. ';
				if (entry["qpf_allday"]["mm"] > 0) description = description + 'Rain '+entry["qpf_allday"]["mm"]+' mm. ';
				if (entry["snow_allday"]["cm"] > 0) description = description + 'Snow '+entry["snow_allday"]["cm"]+' cm. ';
				var item = '<li class="item"><div class="product-img"><img src="static/weather-icons/'+entry["icon"]+'.png"></div><div class="product-info"><a class="product-title">'+title;
				item = item +'<span class="label label-danger pull-right">'+entry["high"]["celsius"]+'°C</span><span class="label label-info pull-right">'+entry["low"]["celsius"]+'°C</span></a>';
				item = item +'<span class="product-description">'+description+'</span></div></li>';
				$("#forecast").append(item);
				if (i == (max_forecast_entries-1)) break;
			}
		});		
	}
	
	// load the almanac
	function load_almanac() {
		$.getJSON("weather/almanac/record/min?start=-1&end=-1&range=1",function(data) {
			load_columnrange_chart('outdoor','Record',parseFloat(data[0][1]),null);
		});
		$.getJSON("weather/almanac/record/max?start=-1&end=-1&range=1",function(data) {
			load_columnrange_chart('outdoor','Record',null,parseFloat(data[0][1]));
		});	
		$.getJSON("weather/almanac/normal/min?start=-1&end=-1&range=1",function(data) {
			load_columnrange_chart('outdoor','Normal',parseFloat(data[0][1]),null);
		});
		$.getJSON("weather/almanac/normal/max?start=-1&end=-1&range=1",function(data) {
			load_columnrange_chart('outdoor','Normal',null,parseFloat(data[0][1]));
		});			
	}
	
	// load alerts
	function load_alerts() {
		$.getJSON("weather/alerts",function(data) {
			PNotify.prototype.options.styling = "fontawesome";
			if (data["forecast"]["precip_time_24hr"] != null) {
				new PNotify({
					title: 'Warning',
					text: data["forecast"]["phrase"],
					type: 'warning'
				});
			}
		});
	}
	
	// load the current condition
	function load_current_condition(sensor,features) {
		// load current condition
		if (features.indexOf("condition") > -1) {
			// retrieve the last measure
			$.getJSON("weather/"+sensor+"/condition/measure?start=-1&end=-1&range=1",function(data) {
				var hour = new Date(data[0][0]).getHours();
				var night = "";
				if (hour >= 20 || hour <= 6) night = "nt_";
				// update the icon
				$("#"+sensor+"_icon").attr("src","static/weather-icons/"+night+data[0][1]+".png");
			});
		}
		// load current temperature and timestamp
		if (features.indexOf("temperature") > -1) {
			// retrieve the last measure
			$.getJSON("weather/"+sensor+"/temperature/measure?start=-1&end=-1&range=1",function(data) {
				// update the timestamp
                $("#"+sensor+"_timestamp").html(timeSince(new Date(data[0][0])));
				// update the temperature
				$("#"+sensor+"_temperature").html(data[0][1]+" °C");
			});
		}
		// load yesterday min temperature
		if (features.indexOf("yesterday_min") > -1) {
			// retrieve the last measure
			$.getJSON("weather/"+sensor+"/temperature/day:min?start=-1&end=-1&range=1",function(data) {
				// update the temperature
				load_columnrange_chart(sensor,'Yesterday',data[0][1],null);
			});
		}
		// load yesterday max temperature
		if (features.indexOf("yesterday_max") > -1) {
			// retrieve the last measure
			$.getJSON("weather/"+sensor+"/temperature/day:max?start=-1&end=-1&range=1",function(data) {
				// update the temperature
				load_columnrange_chart(sensor,'Yesterday',null,data[0][1]);
			});
		}
		// load today min temperature
		if (features.indexOf("today_min_max") > -1) {
			var today = new Date();
			today.setHours(0,0,0,0);
			// retrieve all the measures since midnight
			$.getJSON("weather/"+sensor+"/temperature/hour?start="+parseInt(today.getTime()/1000),function(data) {
				var min = null; var max = null;
				// calculate min and max
				for (i = 0; i < data.length; i++) {
					if (min == null || data[i][1] < min) min = data[i][1];
					if (max == null || data[i][1] > max) max = data[i][1];
				}
				// update the temperature
				load_columnrange_chart(sensor,'Today',min,max);
			});
		}
	}
	
	// retrieve the data and create the series
	function load_timeline_chart(tag,series,history) {
		// clone the default chart options
		var options = $.extend(true,{}, default_chart_options);
		options['xAxis']['type'] = 'datetime';
		options['chart']['zoomType'] = 'x';
		if (! history) {
			options['navigator'] = {'enabled' : false};
			options['rangeSelector'] = {'enabled' : false};
		}
		options['series_counter'] = 0;
		// set the series
		options['series'] = series;
		for (i = 0; i < series.length; i++) {
			// for each series request the data
			$.getJSON(series[i]['url'], function(i,options) {
				return function (data) {
					// set the data
					if (options['series'][i]['type'] == 'flags') {
						flags = [];
						for (j = 0; j < data.length; j++) {
							flags[j] = {'x': data[j][0], 'shape': 'circlepin', 'title': '<img width="20" heigth="20" src="static/weather-icons/'+data[j][1]+'.png">'};
						}
						options['series'][i]['data'] = flags;
					} else options['series'][i]['data'] = data;
					options['series_counter'] += 1;
					// if the data to all the series have been loaded, draw the chart
					if (options['series_counter'] === options['series'].length) $(tag).highcharts('StockChart',options);
				};
			}(i,options));
		}
	}
	
	// load columnrange chart
	function load_columnrange_chart(tag,key,min,max) {
		var series_counter;
		if (tag == "outdoor") series_counter = 8;
		if (tag == "indoor") series_counter = 4;
		// initialize the array
		if (columnrange_data[tag] == null) columnrange_data[tag] = {};
		if (columnrange_data[tag][key] == null) columnrange_data[tag][key] = [];
		// populate with the data provided
		if (min != null) columnrange_data[tag][key][0] = parseFloat(min);
		if (max != null) columnrange_data[tag][key][1] = parseFloat(max);
		var count = 0;
		var x = [];
		var y = [];
		for (i in columnrange_data[tag]) {
			// prepare the data for the chart
			x.push(i);
			y.push(columnrange_data[tag][i]);
			count += columnrange_data[tag][i].length;
			if (columnrange_data[tag][i][0] == null && columnrange_data[tag][i][1] == null) series_counter = series_counter -2;
		}
		// draw the chart
		if (count == series_counter) {
			// setup the chart
			var options = $.extend(true,{}, default_chart_options);
			options['tooltip']['enabled'] = false;
			options['chart']['height'] = 200;
			options['chart']['inverted'] = true;
			options['xAxis']['categories'] = x;
			options['series'] = []
			options['series'][0] = $.extend(true,{}, default_columnrange_options);
			options['series'][0]['data'] = y;
			// draw the chart
			$("#"+tag+"_almanac").highcharts(options);
		}
	}
	
	// load the widgets
	function load() {
		// load current condition widgets
		load_current_condition("outdoor",["condition","temperature","yesterday_min","yesterday_max","today_min_max"]);
		load_current_condition("indoor",["temperature","yesterday_min","yesterday_max","today_min_max"]);
		
		// load the almanac
		load_almanac();

		// load the webcams
		load_webcams();
		
		// load the forecast
		load_forecast();
		
		// load alerts
		load_alerts();

		var recent_start = parseInt(((new Date()).getTime()-24*hour)/1000);
		// outside temperature recent
		series = [];
		series[0] = $.extend(true,{}, default_spline_options);
		series[0]['name'] = "Outside";
		series[0]['id'] = "main";
		series[0]['url'] = "weather/outdoor/temperature/hour?start="+recent_start;
		series[1] = $.extend(true,{}, default_arearange_options);
		series[1]['name'] = "Outside Min/Max";
		series[1]['url'] = "weather/outdoor/temperature/hour:range?start="+recent_start;
		series[2] = $.extend(true,{}, default_flags_options);
		series[2]['url'] = "weather/outdoor/condition/hour?start="+recent_start;
		load_timeline_chart("#outdoor_temperature_recent",series,false);
		
		// inside temperature recent
		series = [];
		series[0] = $.extend(true,{}, default_spline_options);
		series[0]['name'] = "Inside";
		series[0]['lineColor'] = "#000000";
		series[0]['url'] = "weather/indoor/temperature/hour?start="+recent_start;
		series[1] = $.extend(true,{}, default_arearange_options);
		series[1]['name'] = "Inside Min/Max";
		series[1]['url'] = "weather/indoor/temperature/hour:range?start="+recent_start;
		load_timeline_chart("#indoor_temperature_recent",series,false);
		
		// load temperatures history charts
		var history_start = parseInt(((new Date()).getTime()-365*day)/1000);
		
		// outside temperature history
		series = [];
		series[0] = $.extend(true,{}, default_spline_options);
		series[0]['name'] = "Outside";
		series[0]['id'] = "main";
		series[0]['url'] = "weather/outdoor/temperature/day?start="+history_start;
		series[1] = $.extend(true,{}, default_arearange_options);
		series[1]['name'] = "Outside Min/Max";
		series[1]['url'] = "weather/outdoor/temperature/day:range?start="+history_start;
		series[2] = $.extend(true,{}, default_flags_options);
		series[2]['url'] = "weather/outdoor/condition/day?start="+history_start;
		series[3] = $.extend(true,{}, default_spline_options);
		series[3]['name'] = "Record Min";
		series[3]['color'] = "blue";
		series[3]['marker'] = {};
		series[3]['dataLabels'] = {};
		series[3]['dataLabels']['enabled'] = false;
		series[3]['dashStyle'] = "ShortDash";
		series[3]['lineWidth'] = 1;
		series[3]['linkedTo'] = ':previous'
		series[3]['url'] = "weather/almanac/record/min?start="+history_start;
		series[4] = $.extend(true,{}, default_spline_options);
		series[4]['name'] = "Record Max";
		series[4]['color'] = "red";
		series[4]['marker'] = {};
		series[4]['dataLabels'] = {};
		series[4]['dataLabels']['enabled'] = false;
		series[4]['dashStyle'] = "ShortDash";
		series[4]['lineWidth'] = 1;
		series[4]['linkedTo'] = ':previous'
		series[4]['url'] = "weather/almanac/record/max?start="+history_start;
		load_timeline_chart("#outdoor_temperature_history",series,true);
		
		// inside temperature history
		series = [];
		series[0] = $.extend(true,{}, default_spline_options);
		series[0]['name'] = "Inside";
		series[0]['url'] = "weather/indoor/temperature/day?start="+history_start;
		series[0]['lineColor'] = "#000000";
		series[1] = $.extend(true,{}, default_arearange_options);
		series[1]['name'] = "Inside Min/Max";
		series[1]['url'] = "weather/indoor/temperature/day:range?start="+history_start;
		load_timeline_chart("#indoor_temperature_history",series,true);
	}
	
	// load the page
//	load();
	load_test();
	
	// refresh the page
	//setInterval(function(){
	//	load();
	//}, refresh_seconds*1000);

	
	
});
