
from git import *

import re
import os
import glob
import hashlib
import uuid
import urllib
import subprocess
import signal
import calendar, datetime

import string, cgi, time
import threading
import json
import ssl
import socket
import sys, getopt

from repeater import *

from io import StringIO
from xml.dom.minidom import Document
from decimal import Decimal

from os import curdir, sep

from threading import Timer
from threading import Thread
from time import sleep

class AppWrapper:
	
	@property
	def epoch(self):
		return int(time.time())
	
	def log(self, message, scope="App", isError=False):
		
		if (self.debug == 1):
			
			now_ = datetime.datetime.now()
			nowString = now_.strftime("%Y-%m-%d %H:%M:%S")

			if isError:
				print("\033[31m%s\033[0m [\033[36m%s | %s\033[0m]: %s" % (nowString, self.__class__.__name__, scope, message))
			else:
				print("\033[37m%s\033[0m [\033[36m%s | %s\033[0m]: %s" % (nowString, self.__class__.__name__, scope, message))

	def checkRepoState(self, repository):

		if repository == None:
			return
		
		if self.checking:
			return
		
		self.checking = True

		head_ = repository.heads.master
		remotes_ = repository.remotes
		
		if len(remotes_) > 0:
			
			remoteName_ = remotes_[0].name
			remoteinfo_ = repository.remote(remoteName_)

			# we need to update as the remote may have changed...
			# self.log("Remote-url = %s" % remoteinfo_.url, "Checking Repo")
			remoteinfo_.update()
			
			loghead_ = head_.log()
			logremote_ = remoteinfo_.refs[head_.name].log()
			changes_ = False
			
			# log params = .newhexsha, time[0], message, actor, actor.email,
			
			if len(logremote_) > 0 and len(loghead_) > 0:
	
				localSHA_ = loghead_[-1].newhexsha
				remoteSHA_ = logremote_[-1].newhexsha
		
				if (localSHA_ != remoteSHA_):
					self.log("State | local = %s & remote[%s] = %s" % (localSHA_, head_.name, remoteSHA_), "Checking Repo")
					changes_ = True				
				
				if changes_:
					
					self.log("Shutting down app instances!", "Checking Repo", True)
					
					if len(self.apps) > 0:
						for app_ in self.apps:
							
							process_ = app_["process"]

							if (process_ != None):
								self.log("Sending kill process to %d" % process_.pid)
								process_.kill()
								app_["process"] = None
				
					self.log("Sleeping 10 seconds JIC", "Security", True)

					sleep(10)
					
					self.log("Need to fetch updates to local repo", "Checking Repo")
					
					remoteinfo_.pull(head_.name)
		
					self.log("Starting app instances!", "Checking Repo", True)

					if len(self.apps) > 0:						
						for app_ in self.apps:
							app_["process"] = self.startProcess(app_["params"][1::])
		

			else:
				self.log("Repo is bare", "Checking Repo")

		self.checking = False

	def startProcess(self, name=None):
	
		if name == None:
			return
	
		process_ = subprocess.Popen(name)
	
		self.log("Process is running with PID %d" % process_.pid)

		return process_

	def __init__(self, argv):
		
		self.repo = None
		self.process = None
		self.apps = []
		self.poller = None
		self.debug = 0
				
		format = "appwrapper.py -d <0|1>"
		
		try:
			opts, args = getopt.getopt(argv,"hd:",["help","debug="])
		
		except getopt.GetoptError:
			self.log("USAGE: %s" % format)
			sys.exit(2)
	
		for opt, arg in opts:
			
			if opt == "-h":
				print(format)
				sys.exit()
			elif opt in ("-d", "--debug"):
				self.debug = int(arg)
			
		self.log("AppWrapper Created by Samuel D. Colak - Copyright (c)2017 Im-At-Home BV")
		
		# load params in from the config file...
		
		directory_ = os.path.dirname(os.path.abspath(__file__))
			
		with open(("%s/config/app.conf" % (directory_)), 'r', encoding='utf-8') as fileConfig:
			
			for line in fileConfig:
				parts_ = None
				
				if line[-1:] == '\n':
					parts_ = line[:-1].split(",")
				else:
					parts_ = line.split(",")

				self.apps.append({"params":parts_, "process":None})
	
		if len(self.apps) > 0:

			hostname_ = socket.gethostname()
			
			for app_ in self.apps:
				app_["process"] = self.startProcess(app_["params"][1::])
		
		try:
			self.repo = Repo(".", search_parent_directories=True)
			self.checking = False
		
			# poll every 60 seconds
			
			self.poller = Repeater(60.0, self.checkRepoState, self.repo)
			self.poller.start()
		
			while (True):
				sleep(5)

		except KeyboardInterrupt:
	
			self.poller.stop()

			if len(self.apps) > 0:
				
				for app_ in self.apps:
					process_ = app_["process"]
					
					if (process_ != None):
						self.log("Sending kill process to %d" % process_.pid)
						os.kill(process_.pid, signal.SIGINT)
						app_["process"] = None

		except Exception as inst:
			
			exc_type, exc_obj, exc_tb = sys.exc_info()
			print("An exception occurred = [%s:%d] - %s" % (self.__class__.__name__, exc_tb.tb_lineno, inst))

		finally:

			self.log("Closing application")

def main(argv):
	app = AppWrapper(argv)

if __name__ == '__main__':
	main(sys.argv[1:])


