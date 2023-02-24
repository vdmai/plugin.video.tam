# -*- coding: utf-8 -*-
import urllib2, time, cookielib, os

sid_file = os.path.join(os.getcwd(), 'BS.sid')

cj = cookielib.FileCookieJar(sid_file) 
hr  = urllib2.HTTPCookieProcessor(cj) 
opener = urllib2.build_opener(hr)
urllib2.install_opener(opener)


block_sz = 1024#81920

stack = []
buf=None
run_t = 0
comp = 0

'''
from threading import Thread
class MyThread(Thread):
	def __init__(self, resp):
		Thread.__init__(self)
		self.resp = resp
		#self.n = n
	
	def run(self):
		#try:
			global comp
			global buf
			buf=self.resp.read(block_sz)
			comp += 1
		#except:
		#	stack[self.n]=stack[self.n-1]
'''

class BS():
	def __init__(self, url):
		req = urllib2.Request(url)
		self.resp = urllib2.urlopen(req, timeout=1)
		#buf = self.resp.read(block_sz)
		self.last = None#buf
		self.url = url
		self.list = []
		self.run = 0
		self.complit = 0
		self.n = 0
		
		#self.stack = [None,None,None,None,None,None,None,None,None,None]

	def GET(self):
		try: data=self.resp.read(block_sz)
		except: data=None
		#response.close()
		return data

	def get_head(self, url):
		return url[:url.rfind('/')+1]

	def get_data(self):
		print '============= get_data ==============='
		print str(self.n)
		self.n+=1
		
		#if data != None: print 'OK'
		data=self.GET()
		if data!=None:
			if len(data)< 100: data=None
		return data
	
	def create_thread(self, resp):
		print 'create_thread '+str(self.run) +'/'+ str(self.complit)
		#buf=None
		if self.run == self.complit:
			my_thread = MyThread(resp)
			my_thread.start()
			self.run +=1