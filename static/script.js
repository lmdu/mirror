$(document).ready(function(){
	namespace = '/monitor'
	var socket=io.connect('http://'+document.domain+':'+location.port + namespace)

	//socket.on('connect', function(data){
	//	socket.emit('message', 'hello,world');
	//});

	socket.on('weather', function(data){
		$('#location').text(data.city);
		$('#weather-img').attr('src', '/static/img/w/'+data.code+'.png');
		$('#weather-temp').text(data.temperature);
		$('#weather-text').text(data.text);
	});
	
	socket.on('air', function(data){
		$('#weather-wind').text(data.wind);
		$('#humidity').text(data.humidity);
		$('#pressure').text(data.pressure);
		$('#air-quality-level').text(data.level);
		$('#air-quality-aqi').text(data.aqi);
		$('#air-quality-pm25').text(data.pm25);
	});
	
	socket.on('news', function(data){
		$('.news ul').html(data);
	});

	moment.locale('zh-cn');
	update_time();
	setInterval(update_time, 1000);

});

//get the time
function format_time(time){
	if(time<10){
		time = '0'+time
	}
	return time
}
function update_time(){
	var now = moment();
	var second = now.seconds();
	var minute = now.minutes();
	var hour = now.hours();
	$('.second').text(format_time(second));
	$('.minute').text(format_time(minute));
	$('.hour').text(format_time(hour));
	$('.date').text(now.format('dddd MMMMDo'));
}