$(document).ready(function(){
	
	// check the internet status
	function check_internet_status() {
		$.getJSON("https://api.ipify.org/?format=json",function(data) {
			$("#internet_status").html('<i class="fa fa-circle text-success"></i>'+data.ip);
		});
	}
	
	// load sidebar menu
	function load_sidebar_menu() {
		$("#sidebar_menu").empty()
		var menu = '<li class="header">MENU</li><li class="treeview">';
		menu = menu + '<a href="/"> <i class="fa fa-sun-o"></i> <span>Weather</span></a></li>';
		$("#sidebar_menu").html(menu);
	}
		
	// load the widgets
	function load() {
		load_sidebar_menu();
		check_internet_status();
	}

	// load the page
	load();	
});