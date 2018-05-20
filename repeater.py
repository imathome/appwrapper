
import re
import os
import glob
import hashlib
import uuid
import urllib
import socket
import socketserver
import calendar, datetime

import string, cgi, time
import threading
import json
import ssl
import sys, getopt

from io import StringIO
from xml.dom.minidom import Document
from decimal import Decimal

from os import curdir, sep

from threading import Timer
from threading import Thread
from time import sleep

class Repeater(Thread):
	
	def __init__(self, interval, action, args):
		
		Thread.__init__(self)
		self.interval=interval
		self.action=action
		self.args=args
		self.keep_going=True
	
	def run(self):
		while (self.keep_going):
			sleep(self.interval)
			if self.keep_going:
				self.action(self.args)

	def stop(self):
		self.keep_going=False
