#! /usr/bin/python3

from twisted.internet import reactor, endpoints
from twisted.web.resource import Resource
from gpiozero import Button, LightSensor
from twisted.web.server import Site
from time import sleep
import threading
import gpiozero
import datetime
import time
import cgi

RELAY_PIN = 23
DOOR_CLOSED_PIN = 17
DOOR_OPEN_PIN = 16
LIGHTSENSOR_PIN = 21
WALL_SWITCH_PIN = 5

class GaragePage(Resource):

	def __init__(self):
		self.controller = Controller()
		self.last_action_state = None
		self.last_action_time = datetime.datetime.now()

	def render_GET(self, request):
		self.last_action_state = self.controller.get_last_action()
		self.last_action_time = datetime.datetime.now()

		if self.last_action_state == "opened":
			return(b"<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1.0' charset='utf-8'><title>Garage</title></head><body><big><big><big><big><p>The door was <b>" + self.last_action_state.encode('utf-8') + b"</b><br> as of <b>" + ((self.last_action_time.strftime('%I:%M %p')).encode('utf8')) + b"<br>" + ((self.last_action_time.strftime('%a %B %d')).encode('utf8')) + b"</b></p><form method='POST'><input name='change_state' type='submit' value='Close' align='center' style='background-color:#4CAF50; border:none; color:white; display:inline-block; text-decoration:none; height:100px; width:100px; font-size:28px'></form>")
		elif self.last_action_state == "closed" or self.last_action_state == "cracked":
			return(b"<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1.0' charset='utf-8'><title>Garage</title></head><body><big><big><big><big><p>The door was <b>" + self.last_action_state.encode('utf-8') + b"</b><br> as of <b>" + ((self.last_action_time.strftime('%I:%M %p')).encode('utf8')) + b"<br>" + ((self.last_action_time.strftime('%a %B %d')).encode('utf8')) + b"</b></p><form method='POST'><input name='change_state' type='submit' value='Open' align='center' style='background-color:#4CAF50; border:none; color:white; display:inline-block; text-decoration:none; height:100px; width:100px; font-size:28px'></form>")

	def render_POST(self, request):
		print('page posted')
		self.controller.toggle_door()
		self.last_action_time = datetime.datetime.now()
		self.last_action_state = self.controller.get_last_action()

		if self.last_action_state == "opened":
			return(b"<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1.0' charset='utf-8'><title>Garage</title></head><body><big><big><big><big><p>The door was <b>" + self.last_action_state.encode('utf-8') + b"</b><br> as of <b>" + ((self.last_action_time.strftime('%I:%M %p')).encode('utf8')) + b"<br>" + ((self.last_action_time.strftime('%a %B %d')).encode('utf8')) + b"</b></p><form method='POST'><input name='change_state' type='submit' value='Close' align='center' style='background-color:#4CAF50; border:none; color:white; display:inline-block; text-decoration:none; height:100px; width:100px; font-size:28px'></form>")
		elif self.last_action_state == "closed" or self.last_action_state == "cracked":
			return(b"<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1.0' charset='utf-8'><title>Garage</title></head><body><big><big><big><big><p>The door was <b>" + self.last_action_state.encode('utf-8') + b"</b><br> as of <b>" + ((self.last_action_time.strftime('%I:%M %p')).encode('utf8')) + b"<br>" + ((self.last_action_time.strftime('%a %B %d')).encode('utf8')) + b"</b></p><form method='POST'><input name='change_state' type='submit' value='Open' align='center' style='background-color:#4CAF50; border:none; color:white; display:inline-block; text-decoration:none; height:100px; width:100px; font-size:28px'></form>")

class Controller():

	def __init__(self):
		self.door_open_button = Button(DOOR_OPEN_PIN)
		self.door_closed_button = Button(DOOR_CLOSED_PIN)
		self.relay = gpiozero.OutputDevice(RELAY_PIN, active_high=False,initial_value=False)
		self.wall_switch = Button(WALL_SWITCH_PIN)
		self.thread = threading.Thread(target=self.wall_input).start()
		self.lock = threading.Lock()
		self.ldr = LightSensor(LIGHTSENSOR_PIN)

		print('Controller class intialized:' + time.strftime('%I:%M:%S %p %A, %B %d'))
		print('1light detected:' + str(self.ldr.light_detected))

	def wall_input(self):
		print('wall input testing intialized:' + time.strftime('%I:%M:%S %p %A, %B %d'))
		while True:
			sleep(.1)
			print(self.wall_switch.is_pressed)
			if self.wall_switch.is_pressed:
				self.lock.acquire()
				self.toggle_door()
				self.lock.release()

	def get_last_action(self):
		if self.door_open_button.is_pressed:
			print('Door is open: ' + time.strftime('%I:%M:%S %p %A, %B %d'))
			return "opened"
		elif self.door_closed_button.is_pressed:
			print('Door is closed: ' + time.strftime('%I:%M:%S %p %A, %B %d'))
			return "closed"
		else:
			print('Door is cracked: ' + time.strftime('%I:%M:%S %p %A, %B %d'))
			return "cracked"

	def toggle_door(self):
		#print('2light detected:' + str(self.ldr.light_detected))
		if self.door_open_button.is_pressed:
			now = time.time()
			future = now + 12
			print('Closing door: ' + time.strftime('%I:%M:%S %p %A, %B %d'))
			self.toggle_relay()

			while time.time() < future:
					#print(not self.ldr.light_detected)
					#print(self.ldr.value)
					sleep(.05)
					#print('wall switch pressed: ' + str(self.wall_switch.is_pressed))
					if self.wall_switch.is_pressed:
						self.toggle_relay()
						break

					if not self.ldr.light_detected:
						print('Beam crossed: ' + time.strftime('%I:%M:%S %p %A, %B %d'))
						self.toggle_relay()
						sleep(12)
						break
		else:
			print('Opening door: ' + time.strftime('%I:%M:%S %p %A, %B %d'))
			self.toggle_relay()
			now = time.time()
			future = now + 12
			while time.time() < future:
				if self.wall_switch.is_pressed:
					self.toggle_relay()
					break

	def toggle_relay(self):
		self.relay.on()
		sleep(.25)
		self.relay.off()


root = Resource()
root.putChild(b"", GaragePage())
factory = Site(root)
endpoint = endpoints.TCP4ServerEndpoint(reactor, 8880)
endpoint.listen(factory)
reactor.run()
