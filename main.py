import socket
import network
import utime
import time
import board
import adafruit_lis3dh
import busio
import bitbangio
from umqtt.simple import MQTTClient



'''
Define the main class that handles the logic for this
'''
class DogSensor(object):

	def __init__(self, ssid, password, adafruit_username, adafruit__aio_key, adafruit_feed_key):
		self.debug = True;
		self.station = network.WLAN(network.STA_IF)
		self.ssid = ssid
		self.password = password
		self.adafruit_feed_key = adafruit_feed_key
		self.lastCallTime = 0
		self.lastCheckIn = 0
		self.minBetweenCalls = 0.5
		self.minBetweenCheckIn = 60
		myMqttClient = 'dog-sensor-mqtt-client'
		adafruit_io_url = 'io.adafruit.com'
		adafruit_username = adafruit_username
		adafruit__aio_key = adafruit__aio_key
		self.c = MQTTClient(myMqttClient, adafruit_io_url, 0, adafruit_username, adafruit__aio_key)
		self.c.connect()

		# Software I2C setup:
		self.i2c = bitbangio.I2C(board.SCL, board.SDA)
		self.lis3dh = adafruit_lis3dh.LIS3DH_I2C(self.i2c)

		# Set range of accelerometer (can be RANGE_2_G, RANGE_4_G, RANGE_8_G or RANGE_16_G).
		self.lis3dh.range = adafruit_lis3dh.RANGE_2_G

		# Set click detection to double and single clicks.  The first parameter is a value:
		#  - 0 = Disable click detection.
		#  - 1 = Detect single clicks.
		#  - 2 = Detect single and double clicks.
		# The second parameter is the threshold and a higher value means less sensitive
		# click detection.  Note the threshold should be set based on the range above:
		#  - 2G = 40-80 threshold
		#  - 4G = 20-40 threshold
		#  - 8G = 10-20 threshold
		#  - 16G = 5-10 threshold
		self.lis3dh.set_click(2, 80)



	'''
	Main entry point for the class
	'''
	def run(self):
		while True:
			if self.debug:
				print("Running")

			# If not connected to wifi, connect
			if self.station.isconnected() == False:
				self.connectWifi()

			else:
				if self.debug:
					print("Already connected to Wifi")

				# Check if it's time to create another hit
				if self.enoughTimeBetweenCalls():
					if self.isShaking():
						self.createHit()

	'''
	Connect to the wifi, set the clock time
	'''
	def connectWifi(self):
		print("Connecting to Wifi")
		self.station.active(True)
		self.station.connect(self.ssid, self.password)

		# Wait for it to connect
		while self.station.isconnected() == False:
			pass


	'''
	Is the device shaking
	'''
	def isShaking(self):
		x, y, z = self.lis3dh.acceleration
		minG = 1.11

		if self.debug:
			print('x = {}G, y = {}G, z = {}G'.format(x / 9.806, y / 9.806, z / 9.806))

		return True if x / 9.806 > minG or y / 9.806 > minG or z / 9.806 > minG else False


	'''
	Has enough time passed between calls
	'''
	def enoughTimeBetweenCalls(self):
		minSecondsElapsed = self.minBetweenCalls * 60
		now = utime.time()

		if self.lastCallTime == 0:
			self.lastCallTime = utime.localtime(now)
			return False

		else:
			secondsElapsed = self.secondsBetweenTimes(utime.localtime(now), self.lastCallTime)

			if self.debug:
				print("Seconds elapsed")
				print(secondsElapsed)

			return True if secondsElapsed > minSecondsElapsed else False


	'''
	Send a request to the server notifying it to record a "hit"
	'''
	def createHit(self):
		if self.debug:
			print("Creating Hit")

		# Set the last call time as now
		now = utime.time()
		self.lastCallTime = utime.localtime(now)

		# Make the call to adafruit IO
		self.c.connect()
		self.c.publish('stevenquinn/feeds/' + self.adafruit_feed_key, '1')
		self.c.disconnect()


	'''
	Get the number of seconds between two times
	'''
	def secondsBetweenTimes(self, t2, t1):
		deltaH = t2[3] - t1[3]
		deltaM = t2[4] - t1[4]
		deltaS = t2[5] - t1[5]

		return (deltaH * 60 * 60) + (deltaM * 60) + deltaS



'''
Start the main program
'''
wifi_ssid         = 'YOUR WIFI NAME'
wifi_password     = 'YOUR_WIFI_PASSWORD'
adafruit_username = 'YOUR_USERNAME'
adafruit__aio_key = 'YOUR_KEY'
adafruit_feed_key = 'FEED_KEY'

d = DogSensor(wifi_ssid, wifi_password, adafruit_username, adafruit__aio_key, adafruit_feed_key)
d.run()
