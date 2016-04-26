#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import time
import datetime
import StringIO
import socketio #python-socketio module
import requests
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from selenium import webdriver

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

socket = socketio.Server()

app = Flask(__name__)
app.config.update(dict(DEBUG = True))
app.wsgi_app = socketio.Middleware(socket, app.wsgi_app)

#define cache for refresh
weather_cache = None
air_cache = None
news_cache = None

@app.route('/')
def index():
	return render_template('index.html')

@socket.on('connect', namespace='/monitor')
def connect(sid, environ):
	get_weather()
	get_news()

def get_weather():
	global weather_cache
	weather_api = 'https://api.thinkpage.cn/v3/weather/now.json'
	r = requests.get(weather_api, params={'key': 'ijv8jepbqmsjl2pz', 'location': 'ip'})
	
	if r.status_code != requests.codes.ok:
		eventlet.sleep(10)
		get_weather()

	data = r.json()['results'][0]

	weather = dict(
		city = data['location']['name'],
		text = data['now']['text'],
		code = data['now']['code'],
		temperature = data['now']['temperature']
	)

	if weather != weather_cache:
		socket.emit('weather', weather, namespace='/monitor')
		weather_cache = weather

def get_air():
	global air_cache
	driver = webdriver.PhantomJS()
	driver.implicitly_wait(10)
	driver.get('http://www.thinkpage.cn/weather/city/CHSC000000')
	try:
		air = dict(
			wind = driver.find_element_by_css_selector('#ltlSpeed .value').text,
			humidity = driver.find_element_by_css_selector('#ltlHumidity .value').text,
			pressure = driver.find_element_by_css_selector('#ltlPressure .value').text,
			pm25 = driver.find_element_by_id('air-quality-pm25').text,
			aqi = driver.find_element_by_id('air-quality-aqi').text,
			level = driver.find_element_by_id('air-quality-level').text
		)
		
		if air != air_cache:
			socket.emit('air', air, namespace='/monitor')
			air_cache = air

	except:
		eventlet.sleep(10)
		get_humidity_air_quality()

	finally:
		driver.quit()
		
def get_news():
	global news_cache
	news_api = 'http://news.qq.com/newsgn/rss_newsgn.xml'
	r = requests.get(news_api)

	if r.status_code != requests.codes.ok:
		eventlet.sleep(10)
		get_news()
	
	content = r.text.encode('utf-8').replace('gb2312', 'utf-8')

	utf8_parser = ET.XMLParser(encoding='utf-8')
	tree = ET.parse(StringIO.StringIO(content), parser=utf8_parser)
	
	news = [item.find('title').text for item in tree.iter(tag='item')]
	news = map(lambda x: '<li>%s</li>' % x, news[0:5])
	news = "\n".join(news)

	if news != news_cache:
		socket.emit('news', news, namespace='/monitor')
		news_cache = news


def get_baidu_api(url, **kwargs):
	headers = {'apikey': 'bf97b91acf252b36a509fcec206d5a75'}
	r = requests.get(url, params=kwargs, headers=headers)
	if r.status_code != requests.codes.ok:
		return None
	else:
		return r.json()


if __name__ == '__main__':
	scheduler = BackgroundScheduler()
	scheduler.add_job(get_weather, 'interval', seconds=30)
	scheduler.add_job(get_air, 'interval', seconds=120)
	scheduler.add_job(get_news, 'interval', seconds=30)
	scheduler.start()
	eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
