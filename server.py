# coding: utf-8
# Module: server
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import threading
import sys, os
import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import time
import base64
import settings
import proxy_list


if sys.version_info.major > 2:  # Python 3 or later
	import socketserver as SocketServer
	import http.server as BaseHTTPServer
	
	import urllib.request
	from urllib.parse import quote
	from urllib.parse import unquote
	import urllib.request as urllib2
else:  # Python 2
	import BaseHTTPServer, SocketServer
	import urllib, urlparse
	from urllib import quote
	from urllib import unquote
	import urllib2

import ssl
try:
	ctx = ssl.create_default_context()
	ctx.check_hostname = False
	ctx.verify_mode = ssl.CERT_NONE
except: pass

def abortRequested():
	if sys.version_info.major > 2: return xbmc.Monitor().abortRequested()
	else: return xbmc.abortRequested

__settings__ = xbmcaddon.Addon(id='plugin.video.tam')
port = 8095 #int(__settings__.getSetting("serv_port"))

addon = xbmcaddon.Addon(id='plugin.video.tam')

if __settings__.getSetting("Debug")=='true':
	deb = True
	proxy_list.deb = True
else:
	deb = False

cache_dict = {}
gtm=time.time()

# - ====================================== antizapret ====================================================
#import cookielib
#sid_file = os.path.join(xbmc.translatePath('special://temp/'), 'servtam.sid')
#cj = cookielib.FileCookieJar(sid_file) 
#hr  = urllib2.HTTPCookieProcessor(cj) 
def b2s(s):
	if err_torrent(s)==False: return s
	if sys.version_info.major > 2:
		try:s=s.decode('utf-8')
		except: pass
		try:s=s.decode('windows-1251')
		except: pass
		return s
	else:
		return s

def err_torrent(t):
	torrent_data = repr(t)
	if 'd8:' not in torrent_data and 'd7:' not in torrent_data and ':announc' not in torrent_data: True
	else: return False


LOG=[]
def LOG_append(t):
	try:
		if '/log/' not in t:
			tm=str(time.time())+' '
			LOG.append(tm+t)
			if len(LOG)>1000: LOG.pop(0)
	except: pass

def deb_print(s):
	if deb: print(s)
	LOG_append(s)

def CRC32(buf):
		import binascii
		if sys.version_info.major > 2: buf = (binascii.crc32(buf.encode('utf-8')) & 0xFFFFFFFF)
		else: buf = (binascii.crc32(buf) & 0xFFFFFFFF)
		r=str("%08X" % buf)
		return r

AL = ["http://acg.rip:6699/announce","http://open.acgnxtracker.com:80/announce","http://open.acgtracker.com:1096/announce","http://opentracker.i2p.rocks:6969/announce","http://pow7.com:80/announce","http://tracker.gbitt.info:80/announce","http://tracker.internetwarriors.net:1337/announce","http://tracker.kamigami.org:2710/announce","http://tracker.lelux.fi:80/announce","http://tracker.nyap2p.com:8080/announce","http://tracker.torrentyorg.pl:80/announce","http://tracker.yoshi210.com:6969/announce","http://tracker01.loveapp.com:6789/announce","http://tracker1.itzmx.com:8080/announce","http://tracker2.itzmx.com:6961/announce","http://tracker3.itzmx.com:6961/announce","http://tracker4.itzmx.com:2710/announce","http://vps02.net.orel.ru:80/announce","http://www.loushao.net:8080/announce","http://www.proxmox.com:6969/announce","https://tracker.gbitt.info:443/announce","https://tracker.lelux.fi:443/announce","https://tracker.parrotlinux.org:443/announce","udp://bt2.54new.com:8080/announce","udp://qg.lorzl.gq:2710/announce","udp://tr.bangumi.moe:6969/announce","udp://tracker.kamigami.org:2710/announce","udp://tracker.swateam.org.uk:2710/announce","udp://tracker2.itzmx.com:6961/announce","udp://tracker4.itzmx.com:2710/announce","http://h4.trakx.nibba.trade:80/announce","http://mail2.zelenaya.net:80/announce","http://retracker.sevstar.net:2710/announce","http://t.nyaatracker.com:80/announce","http://tracker.bt4g.com:2095/announce","http://tracker.bz:80/announce","http://tracker.corpscorp.online:80/announce","http://tracker.opentrackr.org:1337/announce","http://tracker.tvunderground.org.ru:3218/announce","https://tracker.nanoha.org:443/announce","https://tracker.opentracker.se:443/announce","https://zqzx.xyz:443/announce","udp://bt.okmp3.ru:2710/announce","udp://bt1.archive.org:6969/announce","udp://bt2.archive.org:6969/announce","udp://chihaya.toss.li:9696/announce","udp://open.nyap2p.com:6969/announce","udp://opentracker.i2p.rocks:6969/announce","udp://retracker.akado-ural.ru:80/announce","udp://retracker.netbynet.ru:2710/announce","udp://tracker-udp.gbitt.info:80/announce","udp://tracker.dler.org:6969/announce","udp://tracker.ds.is:6969/announce","udp://tracker.filemail.com:6969/announce","udp://tracker.iamhansen.xyz:2000/announce","udp://tracker.lelux.fi:6969/announce","udp://tracker.nextrp.ru:6969/announce","udp://tracker.nyaa.uk:6969/announce","udp://tracker.sbsub.com:2710/announce","udp://tracker.tvunderground.org.ru:3218/announce","udp://tracker.uw0.xyz:6969/announce","udp://tracker.yoshi210.com:6969/announce","udp://tracker.zum.bi:6969/announce","udp://tracker3.itzmx.com:6961/announce","udp://xxxtor.com:2710/announce","udp://zephir.monocul.us:6969/announce","http://explodie.org:6969/announce","udp://explodie.org:6969/announce","udp://opentor.org:2710/announce","udp://valakas.rollo.dnsabr.com:2710/announce","udp://open.demonii.si:1337/announce","udp://ipv4.tracker.harry.lu:80/announce","udp://retracker.lanta-net.ru:2710/announce","udp://tracker.cyberia.is:6969/announce","udp://tracker.moeking.me:6969/announce","udp://tracker.torrent.eu.org:451/announce","udp://denis.stalker.upeer.me:6969/announce","udp://open.stealth.si:80/announce","udp://tracker.tiny-vps.com:6969/announce","udp://exodus.desync.com:6969/announce","udp://tracker.openbittorrent.com:80/announce","udp://9.rarbg.me:2710/announce","udp://9.rarbg.to:2710/announce","udp://p4p.arenabg.com:1337/announce","udp://tracker.internetwarriors.net:1337/announce","udp://tracker.opentrackr.org:1337/announce","udp://tracker.leechers-paradise.org:6969/announce","udp://tracker.coppersurfer.tk:6969/announce"]


def editor(url):
	deb_print(url)
	import bencode
	r = GET(url, True)
	metainfo = bencode.bdecode(r)
	metainfo['announce']='http://127.0.0.1:8095/proxy/'+metainfo['announce']
	#announce=''
	announce_list=[]
	if 'announce-list' in metainfo.keys():
		try:
			for ans in metainfo['announce-list']:
				announce_list.append(['http://127.0.0.1:8095/proxy/'+ans[0]])
				announce_list.append([ans[0]])
				#announce=announce+'&tr='+quote('http://127.0.0.1:8095/proxy/'+ans[0])
		except: pass
	
	try:
		for i in AL:
			announce_list.append([i])
	except: pass
		
	metainfo['announce-list'] = announce_list
	tr=bencode.encode(metainfo)
	return tr

deb_print('----- Starting TAM_serv -----')
start_trigger = True


def clear_cache():
	for sign in cache_dict.keys():
		tm = cache_dict[sign]['tm']
		if time.time()-tm>3600: cache_dict.pop(sign)

def get_cache(url, all=False):
	try:
		deb_print('====get_cache===')
		sign = CRC32(url)
		if sign in cache_dict.keys():
			item = cache_dict[sign]
			tm = item ['tm']
			if time.time()-tm>3600*3 and all==False: return ''
			data = eval(item['data'])
			deb_print('====return cache===')
			
			return data
		else: 
			D = get_ch(url)
			data = D['data']
			tm = D['tm']
			if proxy_list.test_data(data) == False: return ''
			if time.time()-tm>3600*3 and all==False: return ''
			deb_print('====return ch===')
			return data
	except: return ''

def set_cache(url, ret):
	if proxy_list.test_data(ret):
		try:
			deb_print('====set_cache===')
			clear_cache()
			sign = CRC32(url)
			tm = time.time()
			data = repr(ret)
			cache_dict[sign]={'data': data, 'tm':tm}
		except: pass


def add_ch(data, url):
	deb_print('=add_ch=')
	if proxy_list.test_data(data):
		try:
			SID = 'get_'+str(CRC32(url))
			deb_print(SID)
			D={}
			D['data'] = data
			D['tm']=time.time()
			settings.set(SID, repr(D))
		except: pass

def get_ch(url):
	deb_print('=get_ch_s=')
	try:
		SID1 = 'get_'+str(CRC32(url))
		SID2 = 'get_'+str(CRC32('http://127.0.0.1:8095/proxy/'+url))
		deb_print(SID1)
		deb_print(SID2)
		try:    D  = eval(settings.get(SID1))
		except: D  = eval(settings.get(SID2))
		data = D['data']
		tm = D['tm']
		deb_print('ok')
		return {'tm':tm, 'data':data}
	except:
		deb_print('no')
		return {'tm':0, 'data':''}

def clear_ch():
	L=settings.keys('get_')
	for key in L:
		try:
			D = eval(settings.get(key))
			tm = D['tm']
			day = 86400
			if time.time()-tm > 30*day: settings.rem(key)
		except:
			settings.rem(key)


def GETdata(url, headers=[], to=5):
		urllib2.install_opener(urllib2.build_opener())
		req = urllib2.Request(url)
		if headers==[]: 
			req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)')
		else:
			for hd in headers:
				try:req.add_header(hd[0], hd[1])
				except:pass
		try:    response = urllib2.urlopen(req, timeout = to)
		except: response = urllib2.urlopen(req, timeout = to, context=ctx)
		link=response.read()
		response.close()
		return link

UPL=[]

# =========================== Базовые функции ================================
def GET(url, wpr=False):
	if 'magnet:' in url: return ''
	if '://' not in url: return ''
	try:
		cache=get_cache(url)
		if cache != '': return cache
		deb_print(url)
		
		headers=get_headers(url)
		if __settings__.getSetting("unlock")=='0':
			deb_print( '------- GET direct ---------')
			ret = GETdata(url, headers)
		elif __settings__.getSetting("unlock")=='2' or wpr:
			deb_print( '------- GET anonim ---------')
			import azpt
			ret = azpt.GET(url)
		else:
			deb_print( '------- GET direct ---------')
			try:
				ret = GETdata(url, headers, to=1)
				tst = proxy_list.test_data(ret)
			except:
				tst = False
			deb_print( tst )
			if tst == False: 
				deb_print( '------- GET proxy ---------')
				ret = proxy_list.GET(url, headers)
		if len(ret)>10: set_cache(url, ret)
		return ret
	except:
		LOG_append('--- ERR > ---'+url)
		return get_cache(url, True)

def POST(target, post=None, referer=''):
	try:
		cache=get_cache(target+repr(post))
		if cache != '': return cache
		headers=get_headers(target)
		if __settings__.getSetting("unlock")=='2': 
			deb_print( '------- POST anonim ---------')
			import azpt
			http = azpt.GET(target)
			set_cache(target, http)
			return http
		else:
			deb_print( '------- POST proxy ---------')
			http = proxy_list.POST(target, post)
			set_cache(target+repr(post), http)
			return http
	except:
			deb_print('POST ERR')
			return get_cache(target+repr(post))


def READ(fn):
	if sys.version_info.major > 2:
		try:
			with xbmcvfs.File(fn) as fl:
				r=fl.read()
		except:
			fl = open(fn, "rb")
			r=fl.read()
			fl.close()
	else:
		#fl = open(fn, "rb")
		fl = xbmcvfs.File(fn)
		r=fl.read()
		fl.close()
	return r


def xt(x):
	try: r = xbmc.translatePath(x)
	except: r = xbmcvfs.translatePath(x)
	return r


def showMessage(heading, message, times = 3000):
	xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")'%(heading, message, times, icon))


def mfind(t,s,e):
	r=t[t.find(s)+len(s):]
	r2=r[:r.find(e)]
	return r2
	

#==================================================================



from threading import Thread
class MyThread(Thread):
	def __init__(self, param):
		Thread.__init__(self)
		self.param = param
	
	def run(self):
		update_Lt(pztv.get_stream(self.param))

def create_thread(param):
		my_thread = MyThread(param)
		my_thread.start()


#===================================================================

def get_on(addres):
		deb_print( addres)
		data='ERR 404'
		if len(addres)>10: pref = addres[:10]
		else:              pref = addres
		
		if '/file/' in pref:
			data = READ(unquote(addres[addres.find('/file/')+6:]))
		if 'torrent/' in pref:
			try:
				id=addres[addres.find('torrent/')+8:]
				url=base64.b64decode(unquote(id))
				data = GET(url)
			except:
				pass
		elif '/log/' in pref:
			data = ''
			for i in LOG:
				data +=i+'\n'
		elif 'proxy/' in pref:
			url=addres[addres.find('proxy/')+6:]
			data = GET(url)
		elif 'unlocker/' in pref:
			url=addres[addres.find('unlocker/')+9:]
			try: data = editor(url)
			except: data = url
		elif 'cache/' in pref:
			url=addres[addres.find('cache/')+6:]
			tmp = GET(url)
			if err_torrent(tmp)==False: data=tmp
			else: 
				proxy_list.reset()
				time.sleep(1)
				tmp =  proxy_list.GET(url)
				if err_torrent(tmp)==False: data=tmp
				else: data = ''
			if data != '': add_ch(data, url)
			else: data=get_ch(url)['data']
			
		elif 'restream/' in pref:
			data='BtS:'+addres[addres.find('restream/')+9:]
		elif len(pref)>4:
			if pref[:4]=='http': data = GET(addres)
		
		return data

headers_db={}

def get_headers(url):
	sign = CRC32(url)
	try:
		if sign in headers_db.keys(): return headers_db[sign]
		else: return []
	except: return []

def set_headers(s, url):
	headers=[]
	keys = ['Cookie', 'User-Agent', 'Accept-Encoding', 'Accept-Language', 'Accept', 'Host', 'Referer', 'Content-Type', 'X-Requested-With', 'Authorization', 'Content-Encoding', 'Content-Length', 'Content-Location', 'Content-Range', 'Content-Type', 'Location']
	for key in keys:
		try:
			if s[key]!=None: 
				if 'urllib' in s[key]: headers.append([key, 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)'])
				else: headers.append([key, s[key]])
		except: pass
	sign = CRC32(url)
	headers_db[sign] = headers
	return headers

# ================================ server =====================================


class HttpProcessor(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_HEAD(self):
		LOG_append('> HEAD')
		self.send_response(200)
		if 'jpg' in self.path or 'png' in self.path: self.send_header('Content-type','application/octet-stream')
		else: self.send_header('Content-type', 'text/html')
		
		self.end_headers()


	def do_POST(self):
		deb_print('> POST')
		deb_print( self.path)
		self.data_string = self.rfile.read(int(self.headers['Content-Length']))
		deb_print(self.data_string)
		LOG_append('> POST: '+self.path+' '+repr(self.data_string))
		set_headers(self.headers, self.path)
		
		addres = self.path
		data = ''
		post = None
		if 'proxy/' in addres:
			url=addres[addres.find('proxy/')+6:]
			post = self.data_string
			data = POST(url, post)
		elif 'http' in addres:
			post = self.data_string
			data = POST(addres, post)
		self.send_response(200)
		self.end_headers()
		LOG_append('< POST: '+str(len(data)))
		try: data = data.encode('utf-8')
		except: pass
		self.wfile.write(data)
	
	def do_GET(self):
		#global gtm
		#if '.jpg' in self.path or '.png' in self.path:
			#if time.time() - gtm<1: time.sleep(0.3)
		#	gtm=time.time()
		deb_print('> GET')
		deb_print(self.path)
		LOG_append('> GET: '+self.path)
		set_headers(self.headers, self.path)
		#self.end_headers()
		data=get_on(self.path)
		#LOG_append(data[:4])
		if data == 'ERR 404':
			self.send_response(404)
		elif data[:4]=='http': 
			self.send_response(302)
			self.send_header('Location', data)
			#self.send_header('content-type','application/octet-stream')


		elif data[:4]=='BtS:': 
			self.send_response(200)
			self.send_header('Content-type', 'application/octet-stream')
			self.send_header('Accept-Ranges', 'bytes')
			#self.send_header('Content-Length', 1024*99999)
			self.end_headers()
			hdr=[['User-Agent', 'VLC 2.0.5'], ['Accept', '*/*'], ['Connection', 'keep-alive']]
			LOG_append('> BtS: 1')
			curl=data[4:]
			LOG_append('> BtS: '+curl)
			try: m3u8 = GETdata(curl,hdr, to=10)
			except: m3u8 = None
			LOG_append('> BtS: m3u8 1')
			if m3u8 == None:
				LOG_append('> BtS: m3u8 2')
				time.sleep(2)
				m3u8 = GETdata(curl)
			LOG_append('> BtS: m3u8 ok')
			ch_list = []
			for i in m3u8.splitlines():
				if '/ace/c/' in i: ch_list.append(i)
			
			for st in ch_list:
				LOG_append(st)
				try:
					part=GETdata(st,hdr, to=360)
					LOG_append('part='+str(len(part)))
					if part !=None: self.wfile.write(part)
				except:
					#time.sleep(1)
				#	try:
				#		LOG_append('> err: 1')
				#		part=GETdata(st,hdr, to=360)
				#		if part !=None: self.wfile.write(part)
				#	except:
					LOG_append('> err: 2')
					break



		else:
			self.send_response(200)
			#self.send_header('content-type','application/octet-stream')
		self.end_headers()
		if '/log/' not in self.path: LOG_append('< GET: '+str(len(data))+" "+ repr(data)[:6])
		
		
		try: data = data.encode('utf-8')
		except: pass
		self.wfile.write(data)

class MyThreadingHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
	pass

errors = False
try:
	serv = MyThreadingHTTPServer(("127.0.0.1", port), HttpProcessor)
	threading.Thread(target=serv.serve_forever).start()
except:
	errors = True
	
if errors:
	deb_print('----- TAM_serv ERROR -----')
else:
	deb_print('----- TAM_serv OK -----')
	#proxy_list.TEST_MT()
	clear_ch()
	n=0
	while not abortRequested():
				xbmc.sleep(4000)
				if n==0: proxy_list.get_list(True)
				n+=1
				if n>1000: n=0
				
deb_print('----- TAM_serv shutdown -----')
try:serv.shutdown()
except:pass

deb_print('----- TAM_serv stopped -----')

