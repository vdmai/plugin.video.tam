# coding: utf-8
import time, sys, settings
deb=False

if sys.version_info.major > 2:  # Python 3 or later
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

def b2s(s):
	if sys.version_info.major > 2:
		if test_torrent(s)==False: return s
		try:s=s.decode('utf-8')
		except: pass
		try:s=s.decode('windows-1251')
		except: pass
		try:s=s.decode('cp437')
		except: pass
		return s
	else:
		return s

def test_torrent(t):
	torrent_data = repr(t)
	if 'd8:' not in torrent_data and 'd7:' not in torrent_data and ':announc' not in torrent_data: True
	else: return False

def deb_print(t):
	if deb: print(t)

try:
	import xbmcaddon
	__settings__ = xbmcaddon.Addon(id='plugin.video.tam')
	mtd = __settings__.getSettings("multithread")
except: 
	mtd = 'true'

def CRC32(buf):
		import binascii
		if sys.version_info.major > 2: buf = (binascii.crc32(buf.encode('utf-8')) & 0xFFFFFFFF)
		else: buf = (binascii.crc32(buf) & 0xFFFFFFFF)
		r=str("%08X" % buf)
		return r


def GETvpn():
		req = urllib2.Request(url = 'https://antizapret.prostovpn.org/proxy.pac')
		req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)')
		resp = urllib2.urlopen(req, timeout=3)
		http = resp.read()
		resp.close()
		return http

def antizapret_update():
	try:
		pac=GETvpn()
		prx=pac[pac.find('PROXY ')+6:pac.find('; DIRECT')]
		settings.set("azpt_serv", prx)
		settings.set("azpt_time", str(time.time()))
		return prx
	except:
		prx=settings.get("azpt_serv")
		if len(prx)<10: prx='https://proxy-nossl.antizapret.prostovpn.org:29976'
		return prx


def get_antizapret():
		try:pt=float(settings.get("azpt_time"))
		except:pt=0
		if time.time()-pt > 36000: 
			return antizapret_update()
		else: 
			prx=settings.get("azpt_serv")
			if len(prx)<10: prx='https://proxy-nossl.antizapret.prostovpn.org:29976'
			return prx


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

def save_cache_prx(prx, url=''):
	host = get_host(url)
	if host!='': id = '_'+str(CRC32(host))
	else: 		id = ''
	try:
		settings.set("prx"+id, prx)
		#settings.set("prx_time", str(time.time()))
	except: pass


def get_cache_prx(url=''):
	#'== get_cache_prx =='
	try: 
		if __settings__.getSettings("unlock") =='3': upx = b2s(__settings__.getSettings("u_proxy"))
		else: upx = ''
	except: upx = ''
	if upx !='' and upx !=None: return upx
	
	host = get_host(url)
	if host!='': id = '_'+str(CRC32(host))
	else:		 id = ''
	try: prx=settings.get("prx"+id)
	except:
		try: prx=settings.get("prx")
		except: prx=''
	
	if prx==None: prx=''
	#prx
	return prx

def get_host(url):
	if '//' in url: url = url[url.find('//')+2:]
	else: return ''
	if '/' in url: url = url[:url.find('/')]
	return url

def save_cache_list(L):
	try:
		if L!=[]:
			settings.set("prx_list", repr(L))
			settings.set("list_time", str(time.time()))
	except: pass

def get_cache_list():
	return []
	#'== get_cache_list =='
	try: L=eval(settings.get("prx_list"))
	except: L=[]
	try: tm=float(settings.get("list_tm"))
	except: tm=0
	dt = time.time()-tm 
	##L
	if dt>600 or L==None or L=='': return []
	else: return L

def add_to_BL(prx):
	if 'antizapret.prostovpn' in prx: return
	try:
		try: L=eval(settings.get("prx_BL"))
		except: L=[]
		L.append({'prx':prx, 'tm':time.time()})
		settings.set("prx_BL", repr(L))
	except: pass

def ext_to_BL(BL=[]): #!!!!------!!!!
	return
	try:
		try: L=eval(settings.get("prx_BL"))
		except: L=[]
		for prx in BL:
			L.append({'prx':prx, 'tm':time.time()})
		settings.set("prx_BL", repr(L))
	except: pass

def get_BL():
	#'== get_BL =='
	try:
		Lp=[]
		Ln=[]
		try: L=eval(settings.get("prx_BL"))
		except: L=[]
		for i in L:
			if time.time()-i['tm']<600: 
				Lp.append(i['prx'])
				Ln.append(i)
		settings.set("prx_BL", repr(Ln))
		##Lp
		return Lp
	except:
		settings.set("prx_BL", repr([]))
		return []


def GET2(url):
		#'==GET2=='
		urllib2.install_opener(opener = urllib2.build_opener())
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)')
		req.add_header('accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9')
		req.add_header('accept-encoding', 'deflate')
		
		response = urllib2.urlopen(req, timeout=5)
		data=b2s(response.read())
		response.close()
		return data

def list_us_proxy():
	#'== us_proxy =='
	html=GET2('https://www.us-proxy.org/')
	LL=[]
	tbody = mfind(html,'<tbody>', '</tbody>')
	L=mfindal(tbody,'<tr><td>',"<td class='hm'>")
	for i in L:
		if len(i)>10:
			LL.append(mfind(i,'<td>','<')+':'+mfind(i,'</td><td>','<'))
	return LL

def list_hidemy():
	html=GET2('https://hidemy.name/ru/proxy-list/')
	LL=[]
	tbody = mfind(html,'<tbody>', '</tbody>')
	L=mfindal(tbody,'<tr><td>',"</td><td><i class")
	for i in L:
		if len(i)>10:
			LL.append(i.replace('</td><td>',':').replace('<tr><td>',''))
	return LL

#deb_print(list_hidemy())

def list_pld():
	html=GET2('https://www.proxy-list.download/api/v1/get?type=http&anon=transparent')#&country=US
	L=html.splitlines()
	return L

def list_htmlweb():
	html=GET2('http://htmlweb.ru/json/proxy/get?short&country_not=RU,UA&api_key=7eda2defb0f113cc791a63a6a948800f')
	L=[]
	D=eval(html)
	for i in range(19):
		L.append(D[str(i)])
	return L

#deb_print(list_htmlweb())
#Есть еще такой список https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt

def list_proxyscrape():#сдох
	html=GET2('https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=3000&ssl=all&anonymity=all')#&country=US
	L=html.splitlines()
	return L

def list_foxtools():#сдох
	BCL=[]#"RU", "CN"]
	L=[]
	jsn = GET2('http://api.foxtools.ru/v2/Proxy')
	Lr=eval(jsn)["response"]["items"]
	for i in Lr:
		country = i["country"]["iso3166a2"]
		if country not in BCL:
			L.append(b2s(i['ip']+":"+str(i['port'])))
	return L

def get_list(test_on=False):
	#deb_print('==get_list==')
	L=get_cache_list()
	if L!=[]: 
		#L
		return L
	else:
		#'==get_new_list=='
		L=['proxy-nossl.antizapret.prostovpn.org:29976', 'proxy.antizapret.prostovpn.org:3128']
		
		try: L.extend(list_pld())
		except: pass
		try: L.extend(list_us_proxy())
		except: pass
		try: L.extend(list_hidemy())
		except: pass
		#try: L.extend(list_htmlweb())
		#except: pass
		L2=[]
		for i in L:
			if i not in L2: L2.append(i)
		if test_on: L2=test_list(L2)
		
		save_cache_list(L2)
		return L2

def test_data(data):
	deb_print ('-test_data-')
	if test_torrent(data)==False: return True
	if data == '': return False
	BL = ['400 Bad Request', 'resources is restricted', ' blocked', 'benningtonschools', ' ограничен ', 'ресурс заблокирован', 'ресурсу заблокирован', 'о защите информации', 'диный реестр', 'дином реестре', 'is not available', 'Apache', 'Payara Server', 'Windows Server', 'fba_login.cgi', '=Response_Body_Start=', 'Denied', 'denied', 'RKN', '.rkn.', '149-ФЗ', '149 ФЗ', 'access code', 'nginx.']
	for i in BL:
		if i in b2s(data):
			deb_print ('test_data FALSE: '+i)
			return False
	deb_print ('test_data OK')
	return True 

def GET2PRX(url, prx, headers=[]):
	#deb_print ('==GET2PRX== '+prx+'>'+url)
	try:
		if prx.find('http')<0 : prx="http://"+prx
		proxy_support = urllib2.ProxyHandler({"http" : prx, "https": prx})
		opener = urllib2.build_opener(proxy_support)
		urllib2.install_opener(opener)
		req = urllib2.Request(url)
		#deb_print ('--Request OK')
		if headers==[]:
			#deb_print ('--headers 1')
			req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36 OPR/46.0.2597.39')
			req.add_header('accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9')
			req.add_header('accept-encoding', 'gzip, deflate')
		else:
			#deb_print ('--headers 2')
			for hd in headers:
				deb_print (hd)
				if hd[1]!=None: req.add_header(hd[0], hd[1])
		#deb_print ('headers OK')
		response = urllib2.urlopen(req, timeout=5)
		#deb_print (response.getcode())
		if response.info().get('Content-Encoding') == 'gzip':
			deb_print ('-- gzip')
			try:
				from StringIO import StringIO # for Python 2
			except:
				from io import BytesIO as StringIO# for Python 3
			import gzip
			tmp = response.read()
			deb_print(repr(tmp)[:100])
			buf = StringIO(tmp)
			f = gzip.GzipFile(fileobj=buf)
			data = f.read()
		else:
			data=response.read()
		response.close()
		deb_print ('==GET2PRX OK==')
		deb_print (repr(data)[:100])
		
		if test_data(data): 
			return data
		else: 
			add_to_BL(prx)
			return ''
	except:
		#deb_print ('except GET2PRX')
		return ''

#deb_print(GET2PRX('http://rutor.is', 'proxy-nossl.antizapret.prostovpn.org:29976'))

def POST2PRX(url, post, prx, headers=[]):
	#'==POST2PRX=='
	try:
		if prx.find('http')<0 : prx="http://"+prx
		proxy_support = urllib2.ProxyHandler({"http" : prx, "https": prx})
		opener = urllib2.build_opener(proxy_support)
		urllib2.install_opener(opener)
		
		if sys.version_info.major > 2: post = post.encode()
		req = urllib2.Request(url, data = post)
		if headers==[]:
			req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36 OPR/46.0.2597.39')
			req.add_header('accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9')
			req.add_header('accept-encoding', 'gzip, deflate')
		else:
			for hd in headers:
				req.add_header(hd[0], hd[1])
		
		response = urllib2.urlopen(req, timeout=5)
		#response.getcode()
		if response.info().get('Content-Encoding') == 'gzip':
			deb_print ('-- gzip')
			try:
				from StringIO import StringIO # for Python 2
			except:
				from io import BytesIO as StringIO# for Python 3
			import gzip
			tmp = response.read()
			deb_print(repr(tmp)[:100])
			buf = StringIO(tmp)
			f = gzip.GzipFile(fileobj=buf)
			data = f.read()
		else:
			data=response.read()
		response.close()
		#'==GET2PRX OK=='
		##repr(data)
		if test_data(data): return data
		else: return ''
	except:
		return ''


def GET(url, headers=[]):
	#'==PL GET=='
	BL = get_BL()
	sprx=get_cache_prx(url)
	
	if sprx!=''and sprx not in BL:
		##'>>>>>>>>>>'
		if mtd == 'true': resp = GET2PRX_MT(url, sprx, headers)
		else:             resp = GET2PRX(url, sprx, headers)
		##'<<<<<<<<<<'
		if len(repr(resp))>10: 
			#'==PL RET>=='
			return resp
		#else: add_to_BL(sprx)
	
	
	if mtd == 'true': return GET_MT(url, headers)
	
	L=get_list()
	
	for prx in L:
		#prx
		if prx not in BL:
			resp = GET2PRX(url, prx, headers)
			if resp!='':
				if TEST_prx(prx):
					save_cache_prx(prx, url)
					return resp
				else:
					add_to_BL(prx)
			else:
				add_to_BL(prx)
	
	#'---end list---'
	return ''


def POST(url, post, headers=[]):
	#'==PL POST=='
	
	BL = get_BL()
	sprx=get_cache_prx(url)
	if sprx!='' and sprx not in BL:
		resp = POST2PRX(url, post, sprx, headers)
		if len(repr(resp))>200:
			#'==cache=='
			##repr(resp)
			return resp
		else:
			add_to_BL(sprx)
	
	if mtd == 'true': return POST_MT(url, headers)
	
	L=get_list()
	##L
	for prx in L:
		#prx
		if prx not in BL:
			resp = POST2PRX(url, post, prx, headers)
			if resp!='': 
				save_cache_prx(prx, url)
				return resp
			else:
				add_to_BL(prx)
	#'---end list---'
	reset()
	return ''

def PROXY(url='http://rutor.is'):
	#'==PL PROXY=='
	BL = get_BL()
	sprx=get_cache_prx()
	if sprx!=''and sprx not in BL:
		resp = GET2PRX(url, sprx)
		if len(repr(resp))>200:
			#'==cache=='
			##repr(resp)
			return sprx
		else:
			add_to_BL(sprx)
	
	sprx=get_antizapret()#'proxy.antizapret.prostovpn.org:3128'
	if sprx not in BL:
		resp = GET2PRX(url, 'sprx')
		if len(repr(resp))>200:
				save_cache_prx('sprx')
				return sprx
		else:
			add_to_BL(sprx)
	
	L=get_list()
	##L
	for prx in L:
		#prx
		if prx not in BL:
			resp = GET2PRX(url, prx)
			if resp!='':
				save_cache_prx(prx, url)
				return prx
			else:
				add_to_BL(prx)
	
	#'---end list---'
	reset()
	return ''

#------------------------------------------------------
Lthread=[]
BLthread=[]
LtID=''
def update_Lt(d, id):
	global Lthread, LtID
	if d == 'reset':
		Lthread=[]
		#LtID = id
	#elif LtID == id:
	elif len(d['data']) > 200 or d['data'][0]=='{': 
		Lthread.append(d)
	else:
		add_to_BL(d['prx'])

from threading import Thread
class MyThread(Thread):
	def __init__(self, param):
		Thread.__init__(self)
		self.param = param
	
	def run(self):
		##"run "+self.param['prx']
		try:    post = self.param['post']
		except: post = ''
		try:    headers = self.param['headers']
		except: headers = []
		if post == '': resp = GET2PRX(self.param['url'], self.param['prx'], headers)
		else:          resp = POST2PRX(self.param['url'], post, self.param['prx'], headers)
		if resp == '': BLthread.append(self.param['prx'])
		else:          update_Lt({'data':resp, 'prx':self.param['prx'], 'id':self.param['id']}, self.param['id'])

def create_thread(param):
		my_thread = MyThread(param)
		my_thread.start()
#---------------------------------------------------
def GET2PRX_MT(url, prx, headers=[]):
	id = CRC32(url)#time.time()
	update_Lt('reset', id)
	create_thread({'url':url, 'prx':prx, 'id':id, 'headers': headers})
	for n in range(50):
			time.sleep(0.1)
			if len(Lthread)>0:
				for i in Lthread:
					if i['id']==id: return i['data']
	return ''


def GET_MT(url, headers=[]):
	#'== GET_MT =='
	BL = get_BL()
	L=get_list()
	L2=[]
	id = CRC32(url)#time.time()
	update_Lt('reset', id)
	total_threads=len(L)
	n=0
	deb_print('create_threads')
	for prx in L:
		if prx not in BL:
			n+=1
			#if n>100: break # примерно 3 сек
			#deb_print('create_thread '+str(n))
			create_thread({'url':url, 'prx':prx, 'id':id, 'headers': headers})
			time.sleep(0.03)
			if len(Lthread)>0:
				for i in Lthread:
					prx = i['prx']
					if prx not in BL and i['id']==id:
						#if len(i['data'])>100:
							save_cache_prx(prx, url)
							#ext_to_BL(BLthread)
							#'== RET_MT1> =='
							return i['data']
						#else:
						#	BL.append(prx)
						#	add_to_BL(prx)
	deb_print('wait_threads')
	for t in range(10):
			deb_print (t)
			time.sleep(0.1)
			if len(Lthread)>0:
				#i=Lthread[0] 
				for i in Lthread:
					prx = i['prx']
					if prx not in BL and i['id']==id:
						#if len(i['data'])>100 :
							save_cache_prx(prx, url)
							#ext_to_BL(BLthread)
							#'== RET_MT2> =='
							return i['data']
						#else:
						#	BL.append(prx)
						#	add_to_BL(prx)
					
	#'-------END :( -------'
	return ''

def POST_MT(url, post, headers=[]):
	BL = get_BL()
	L=get_list()
	L2=[]
	id = CRC32(url)#time.time()
	update_Lt('reset', id)
	total_threads=len(L)
	n=0
	for prx in L:
		if prx not in BL:
			n+=1
			#'create_thread '+str(n)
			create_thread({'url':url, 'prx':prx, 'post':post, 'id':id, 'headers': headers})
			time.sleep(0.03)
			if len(Lthread)>0:
				for i in Lthread:
					prx = i['prx']
					if prx not in BL and i['id']==id:
						#if len(i['data'])>100:
							save_cache_prx(prx, url)
							#ext_to_BL(BLthread)
							return i['data']
						#else:
						#	BL.append(prx)
						#	add_to_BL(prx)
	
	for t in range(20):
			xbmc.sleep(100)
			if len(Lthread)>0: 
				for i in Lthread:
					prx = i['prx']
					if prx not in BL and i['id']==id:
						#if len(i['data'])>100:
							save_cache_prx(prx, url)
							#ext_to_BL(BLthread)
							return i['data']
						#else:
						#	BL.append(prx)
						#	add_to_BL(prx)
	#'-------END :( -------'
	return ''

def TEST_prx(prx):
	return True
	#'-- TEST_prx --'
	url='http://rutor.is'
	resp = GET2PRX(url, prx)
	if 'rutor.info' in resp: return True
	else: return False


def reset():
	save_cache_list([])
	save_cache_prx('')
	settings.set("prx_BL", repr([]))
	get_list()


#------------------------------------------------------
Ltest=[]
def update_Ltest(d):
	global Ltest
	if d == 'reset': Ltest=[]
	else: Ltest.append(d)

from threading import Thread
class MyThread2(Thread):
	def __init__(self, param):
		Thread.__init__(self)
		self.param = param
	
	def run(self):
		if TEST2PRX('http://ya.ru', self.param['prx']): update_Ltest(self.param['prx'])

def create_test(param):
		my_thread2 = MyThread2(param)
		my_thread2.start()
#---------------------------------------------------

def TEST2PRX(url, prx):
	if 'antizapret' in prx: return True
	#deb_print prx
	try:
		if prx.find('http')<0 : prx="http://"+prx
		proxy_support = urllib2.ProxyHandler({"http" : prx, "https": prx})
		opener = urllib2.build_opener(proxy_support)
		urllib2.install_opener(opener)
		req = urllib2.Request(url)
		
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36 OPR/46.0.2597.39')
		req.add_header('accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9')
		req.add_header('accept-encoding', 'gzip, deflate')
		response = urllib2.urlopen(req, timeout=1)
		response.close()
		#deb_print response.getcode()
		if response.getcode() == 200: 
			response.close()
			return True
		else:
			return False
	except:
		return False

def test_list(L):
	update_Ltest('reset')
	for prx in L:
		create_test({'prx': prx})
		time.sleep(0.1)
	
	time.sleep(1)
	return Ltest


#time.time()
#r=GET('http://rutor.is/torrent/892551')
#time.time()
#time.sleep(10)
#deb_print (r[:20])