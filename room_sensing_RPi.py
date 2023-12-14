# GENERAL IMPORTS
import RPi.GPIO as GPIO
import time

# SETUP
# ... api requests
import http.client
import urllib3
from urllib.parse import urlencode
key = "XXXXXXX" #API Key

# ... board
print ("starting")
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# ... temperature and humidity sensor
#import Adafruit_DHT
#DHTSensor = Adafruit_DHT.DHT11
#DHTPin = 4

# ... luminosity sensor
import board
import adafruit_bh1750
i2c = board.I2C()
LUXSensor = adafruit_bh1750.BH1750(i2c)

# ... LED
# ... ... Room presence leds
LedPinOut = 26
LedPinIn = 19
GPIO.setup(LedPinOut, GPIO.OUT)
GPIO.setup(LedPinIn, GPIO.OUT)
# ... ... Api Led
LedPinApi = 18
GPIO.setup(LedPinApi,GPIO.OUT)
def BlinkLED(ledpin):
	GPIO.output(ledpin, GPIO.HIGH)
	time.sleep(1)
	GPIO.output(ledpin, GPIO.LOW)

# ... LIGHT CONTROL
ButtonPin = 23
GPIO.setup(ButtonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
import datetime
import tinytuya
bulb = tinytuya.BulbDevice('XXXXX', 'XX.XX.XX.XX','XXXXXXXX')
bulb.set_version(3.3)
bulb.set_socketPersistent(True)
class lightControl():
	def __init__(self):
		self.sleep_time = False
		self.light_on = False
		self.should_turnoff = "no"

	def button_callback(self, channel):
		if self.sleep_time == False:
			print("ready for sleep, turn light off")
			bulb.turn_off()
			self.light_on = False
			self.sleep_time = True
			BlinkLED(LedPinApi)
			BlinkLED(LedPinApi)
			
	def checkLight(self, light):
		self.turn_lighton(light)
		self.stop_sleeptime()
		self.turn_lightoff()
		print(self.should_turnoff)
		
	
	def stop_sleeptime(self):
		now = datetime.datetime.now()
		today7am = now.replace(hour=12, minute=0, microsecond=0)
		today8am = now.replace(hour=13, minute=0, microsecond=0)
		if now > today7am and now < today8am and self.sleep_time == True:
			self.sleep_time = False
			
	def turn_lighton(self, light):
		if light<35 and movements.in_room == True and self.sleep_time == False and self.light_on == False:
			print("turn light on ")
			bulb.turn_on()
			bulb.set_white(1000, 10)
			self.light_on = True
			
	def turn_lightoff(self):
		if self.should_turnoff == "yes":
			print("turn light off")
			bulb.turn_off()
			self.light_on = False
			self.should_turnoff == "no"
		elif self.should_turnoff == "wait":
			self.should_turnoff = "yes"
		


light_control = lightControl()
GPIO.add_event_detect(ButtonPin, GPIO.RISING, callback=light_control.button_callback)

# ... PIR SENSOR WITH INTERRUPT
PirPin = 13
GPIO.setup(PirPin, GPIO.IN)

class Movements:
	def __init__(self):
		self.in_room = True
		self.mymoves = 2
		self.canundo = False

	def MOTION(self, PirPin):
		print("motion detected")
		if self.in_room == True:
			self.in_room = False
			GPIO.output(LedPinIn,GPIO.LOW)
			GPIO.output(LedPinOut,GPIO.HIGH)
			self.mymoves = self.mymoves*10
			light_control.should_turnoff = "wait"
		elif self.in_room == False:
			self.in_room = True
			GPIO.output(LedPinOut,GPIO.LOW)
			GPIO.output(LedPinIn, GPIO.HIGH)
			self.mymoves = self.mymoves*10 + 1
			light_control.should_turnoff = "no"
			light_control.turn_lighton(LUXSensor.lux)
		print(self.mymoves)
		self.canundo = True
	
	def UndoMOTION(self, ButtonPinOut):
		if self.canundo == True:
			print("undo move")
			if self.in_room == True:
				self.in_room = False
				GPIO.output(LedPinIn,GPIO.LOW)
				GPIO.output(LedPinOut,GPIO.HIGH)
				self.mymoves = (self.mymoves-1)/10
				light_control.should_turnoff = "wait"
			elif self.in_room == False:
				self.in_room = True
				GPIO.output(LedPinOut,GPIO.LOW)
				GPIO.output(LedPinIn, GPIO.HIGH)
				self.mymoves = self.mymoves/10
				light_control.should_turnoff = "no"
				light_control.turn_lighton(LUXSensor.lux)
			print("new: ",self.mymoves)
			self.canundo = False

movements = Movements()
GPIO.add_event_detect(PirPin, GPIO.RISING, callback=movements.MOTION)
GPIO.output(LedPinIn, GPIO.HIGH)
print ("pir module ready")

# ... UNDO MOVE BUTTON
ButtonPinUndo = 24
GPIO.setup(ButtonPinUndo, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(ButtonPinUndo, GPIO.RISING, callback=movements.UndoMOTION)


# MAIN FUNCTION
def getEnvironment():
	while True:
		#Calculate temperature and humidity
		#humidity, temperature = Adafruit_DHT.read_retry(DHTSensor, DHTPin)
		#Get luminosity
		luminosity = LUXSensor.lux
		light_control.checkLight(luminosity)
		#Alert values were collected
		BlinkLED(LedPinApi)
		#Combine values collected and create api
		params = urlencode({'field3':luminosity, 'field7':movements.mymoves, 'key':key})
		movements.mymoves = 2
		movements.canundo = False
		headers = {"Content-typZZe":"application/x-www-form-urlencoded","Accept": "text/plain"}
		conn = http.client.HTTPConnection("api.thingspeak.com:80")
		try:
			conn.request("POST", "/update", params, headers)
			response = conn.getresponse()
			print (luminosity, 'lux')
			print (response.status, response.reason)
			data = response.read()
			conn.close()
		except:
			print ("connection failed")
		break

try:
	while True:
		getEnvironment()
		time.sleep(300)
except KeyboardInterrupt:
	print("Quit")
	GPIO.output(LedPinIn, GPIO.LOW)
	GPIO.output(LedPinOut, GPIO.LOW)
	GPIO.cleanup()
