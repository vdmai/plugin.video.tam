#!/usr/bin/python
# -*- coding: utf-8 -*-
# - ====================================== antizapret ====================================================
import xbmc, xbmcaddon
import time, cookielib, urllib, urllib2, os, sys
__settings__ = xbmcaddon.Addon(id='plugin.video.tam')
sid_file = os.path.join(xbmc.translatePath('special://temp/'), 'vpn.sid')
cj = cookielib.FileCookieJar(sid_file) 
hr  = urllib2.HTTPCookieProcessor(cj) 

proxy_list=[
	'http://starken.net/index.php?q=',                #тайвань
	'http://arne-post.de/index.php?q=',               #англия
	'http://mutante.awardspace.us/index.php?q=',      #болгария
	'http://www.lolz.eu/z/index.php?q=',              #Англия
	'http://matusik.net/bramka/index.php?q=',         #польша
	'http://www.nanopartian.com/m/index.php?q=',      #германия
	'http://www.mattwpbs.com/runtime/index.php?q=',   #Англия
	'https://www.bnetweb.org/proxy/index.php?q=',     #США
	'http://prx.afkcz.eu/prx/index.php?q=',           #Чехия
	'http://us7.unblock-websites.com/index.php?q=',
	'http://us6.unblock-websites.com/index.php?q=',
	'http://us5.unblock-websites.com/index.php?q=',
	'http://us4.unblock-websites.com/index.php?q=',
	'http://us3.unblock-websites.com/index.php?q=',
	'http://us2.unblock-websites.com/index.php?q=',
	'http://us1.unblock-websites.com/index.php?q=',
]
#	'http://xawos.ovh/index.php?q=',             #Франция
#	'https://derzeko.de/Proxy/index.php?q=',     #Германия
#	'http://thely.fr/proxy/?q=',                 #Франция
#	'http://www.pitchoo.net/zob_/index.php?q=',  #Франция


def test_url(url):
	import urllib2
	try:
		response = urllib2.urlopen(url, timeout=5)
		c=response.getcode()
		if '404' in str(c): return '404'
		elif 'URL Error' in str(c): return '404'
		else: 				return '200'
	except:
		return '404'

def mfindal(http, ss, es):
	L=[]
	while http.find(es)>0:
		s=http.find(ss)
		e=http.find(es,s)
		i=http[s:e]
		L.append(i)
		http=http[e+2:]
	return L

def mfind(t,s,e):
	r=t[t.find(s)+len(s):]
	r2=r[:r.find(e)]
	return r2


def GETdata(url):
		#print url
		urllib2.install_opener(urllib2.build_opener())
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)')
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		return link

'''
def GETvpn():
	import httplib
	conn = httplib.HTTPConnection("antizapret.prostovpn.org")
	conn.request("GET", "/proxy.pac", headers={"User-Agent": 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)'})
	r1 = conn.getresponse()
	data = r1.read()
	conn.close()
	return data
def proxy_update():
	try:
		print 'proxy_update'
		#url='https://antizapret.prostovpn.org/proxy.pac'
		pac=GETvpn()#url)
		prx=pac[pac.find('PROXY ')+6:pac.find('; DIRECT')]
		__settings__.setSetting("proxy_serv", prx)
		__settings__.setSetting("proxy_time", str(time.time()))
	except: 
		print 'except get proxy'

def get_opener():
		try:pt=float(__settings__.getSetting("proxy_time"))
		except:pt=0
		print pt
		if time.time()-pt > 36000: proxy_update()
		prx=__settings__.getSetting("proxy_serv")
		print prx
		if prx.find('http')<0 : prx="http://"+prx
		proxy_support = urllib2.ProxyHandler({"http" : prx})
		opener = urllib2.build_opener(proxy_support, hr)
		#urllib2.install_opener(opener)
		print 'opener ok'
		return opener
'''

def convert(url):
	#print '==convert==='
	import base64
	sign=base64.b64encode(url)
	try: id=int(__settings__.getSetting("proxy_id"))
	except: id=0
	try: tm=float(__settings__.getSetting("proxy_tm"))
	except: tm=0
	dt = time.time()-tm
	#if id!=-1: 
	if dt>360:
			proxy=proxy_list[id]
			#c=test_url(proxy.replace('?q=', ''))
			redir=proxy_list[id]+urllib.quote_plus(sign)
			c = test_url(redir)
	else:
			c='200'
	
	if c=='404':
		for id in range (len(proxy_list)):
				proxy=proxy_list[id]
				#print proxy
				#c=test_url(proxy.replace('?q=', ''))
				#if c!='404': 
				redir=proxy_list[id]+urllib.quote_plus(sign)
				if test_url(redir)!='404':
						__settings__.setSetting("proxy_id", str(id))
						__settings__.setSetting("proxy_tm", str(time.time()))
						break
	
	redir=proxy_list[id]+urllib.quote_plus(sign)
	return redir


def decoder(hp, id=0):
	if ':announce' in hp: return hp
	import base64, urllib
	id=int(__settings__.getSetting("proxy_id"))
	if id=='': id=0
	r=''
	L=hp.splitlines()
	proxy = proxy_list[id]
	for h in L:
		if proxy not in h:
			if 'https:' in proxy: alturl = proxy.replace('https:', 'http:')
			else : alturl = proxy.replace('http:', 'https:')
			if alturl in h: proxy = alturl
		if proxy in h:
			L2=mfindal(h, proxy, '"')
			for i in L2:
				try:
					url=base64.b64decode(urllib.unquote_plus(i.replace(proxy,'')))
					h=h.replace(i, url)
				except:
					print 'ERR'
					print i
			r+=h+'\n'
		else:
			r+=h+'\n'
	return r

def GET(url):
	curl = convert(url)
	#print curl
	data = GETdata(curl)
	dd = decoder(data)
	return dd

def POST(target, post=None):
	import base64
	sign=base64.b64encode(target)
	target = 'http://matusik.net/bramka/index.php?q='+urllib.quote_plus(sign)
	req = urllib2.Request(url = target, data = post)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36 OPR/46.0.2597.39')
	resp = urllib2.urlopen(req)
	http = resp.read()
	resp.close()
	return http
