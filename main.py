# -*- coding: utf-8 -*-

import xbmc, xbmcgui, xbmcplugin, xbmcaddon, os, sys, xbmcvfs, time#, json
import settings

if sys.version_info.major > 2:  # Python 3 or later
	import urllib.request
	from urllib.parse import quote
	from urllib.parse import unquote
	import urllib.request as urllib2
	from urllib.parse import urlencode
else:  # Python 2
	import urllib, urlparse
	from urllib import quote
	from urllib import unquote_plus as unquote
	import urllib2
	from urllib import urlencode

import lt2http as lt2h

PLUGIN_NAME   = 'TAM'
handle = int(sys.argv[1])
addon = xbmcaddon.Addon(id='plugin.video.tam')
__settings__ = xbmcaddon.Addon(id='plugin.video.tam')

Pdir = addon.getAddonInfo('path')
icon = os.path.join(addon.getAddonInfo('path'), 'icon.png')
xbmcplugin.setContent(int(sys.argv[1]), 'movies')
engine_t2h=None
engine_ts=None
index_ts =0


def deb_print(s):
	print(s)

def CRC32(buf):
		import binascii
		if sys.version_info.major > 2: buf = (binascii.crc32(buf.encode('utf-8')) & 0xFFFFFFFF)
		else: buf = (binascii.crc32(buf) & 0xFFFFFFFF)
		r=str("%08X" % buf)
		return r

def ru(x):return unicode(x,'utf8', 'ignore')
def xt(x):
	try: r = xbmc.translatePath(x)
	except: r = xbmcvfs.translatePath(x)
	return r
def f2u(x): return 'file:///'+x.replace('\\','/')

def is_libreelec():
	try:
		if os.path.isfile('/etc/os-release'):
			f = open('/etc/os-release', 'r')
			str = f.read()
			f.close()
			if "LibreELEC" in str and "Generic" in str: return True
	except: pass
	return False

def rt(s):
	if sys.version_info.major > 2: return s
	try:s=s.decode('utf-8')
	except: pass
	if not is_libreelec():
		try:s=s.decode('windows-1251')
		except: pass
	try:s=s.encode('utf-8')
	except: pass
	return s

def b2s(s):
	if err_torrent(s)==False: return s
	if sys.version_info.major > 2:
		try:s=s.decode('utf-8')
		except: pass
		try:s=s.decode('windows-1251')
		except: pass
		try:s=s.decode('cp437')
		except: pass
		return s
	else:
		return s

def err_torrent(t):
	torrent_data = repr(t)
	if 'd8:' not in torrent_data and 'd7:' not in torrent_data and ':announc' not in torrent_data: True
	else: return False

def ut(s):
	try:s=s.decode('utf-8')
	except: pass
	if not is_libreelec():
		try:s=s.decode('windows-1251')
		except: pass
	return s

def zipped(data):
		import StringIO
		import gzip
		out = StringIO.StringIO()
		with gzip.GzipFile(fileobj=out, mode="w") as f:
			f.write(data)
		data=out.getvalue()
		return data

def file2url(fn):
	url='http://127.0.0.1:8095/file/'
	#data = READ(fn)
	#url = POST (url, data)
	url+=quote(fn)
	return url

def add_ch(url, data):
	deb_print('=add_ch=')
	if err_torrent(data): return
	try:
		SID = 'get_'+str(CRC32(url))
		deb_print(SID)
		D={}
		D['data'] = data
		D['tm']=time.time()
		settings.set(SID, repr(D))
	except: pass

def get_ch(url, nt=False):
	deb_print('=get_ch=')
	deb_print(url)
	try:
		SID = 'get_'+str(CRC32(url))
		deb_print(SID)
		D  = eval(settings.get(SID))
		data = D['data']
		tm = D['tm']
		if time.time()-tm>3600*3 and nt==False: 
			deb_print('> old')
			return ''
		deb_print('> ok')
		return data
	except:
		deb_print('> no')
		return ''

def fs_dec(path):
	try:
		sys_enc = sys.getfilesystemencoding() if sys.getfilesystemencoding() else 'utf-8'
		return path.decode(sys_enc).encode('utf-8')
	except:
		return path

def fs_enc(path):
	path=xt(path)
	sys_enc = sys.getfilesystemencoding() if sys.getfilesystemencoding() else 'utf-8'
	try:path2=path.decode('utf-8')
	except: pass
	try:path2=path2.encode(sys_enc)
	except: 
		try: path2=path2.encode(sys_enc)
		except: path2=path
	return path2

LTORRENT_PRELOAD_BYTES = 1024 ** 2 * 64
class LTorrentClient(xbmc.Player):
	def __init__(self):
		super(LTorrentClient, self).__init__()
		self.url = None
		self.opener = urllib2.build_opener()
		self.info_hash = None
		self.torrent_location = None  # type: dict
		self.f_index = 0
		self.is_wait_preload = False

	def lt_request(self, data):
		req = urllib2.Request(urlparse.urljoin(self.url, '/api'), json.dumps(data))
		req.get_method = lambda: 'POST'
		res = self.opener.open(req, timeout=2)
		if res.getcode() == 200:
			return json.loads(res.read())
		else:
			return None

	def lt_open_torrent(self):
		self.torrent_location.update({'action': 'open_torrent'})
		# xbmc.log(str(torrent_location), xbmc.LOGNOTICE)
		res = self.lt_request(self.torrent_location)
		self.info_hash = res['info_hash']

	def lt_open_file(self):
		return self.lt_request({'action': 'open', 'f_index': self.f_index})

	def lt_stop(self):
		return self.lt_request({'action': 'stop'})

	def lt_download_status(self):
		return self.lt_request({'action': 'download_status'})

	def lt_get_file_url(self):
		file_list = self.lt_request({'action': 'get_file_list'})['file_list']
		# xbmc.log(str(file_list), xbmc.LOGNOTICE)
		return urlparse.urljoin(self.url, '/play/%s/%s/%s' % (self.info_hash, self.f_index, file_list[self.f_index]))

	def lt_start_service(self):
		xbmc.executeJSONRPC(json.dumps({
			"jsonrpc": "2.0",
			"method": "JSONRPC.NotifyAll",
			"params": {
				"sender": 'LTorrentClient',
				"message": "StartLTorrent",
			},
			"id": 1
		}))

	def lt_play(self, torrent_location, f_index):
		self.lt_start_service()
		xbmc.sleep(300)  # wait start Engine
		self.torrent_location = torrent_location
		self.f_index = f_index
		self.lt_open_torrent()
		self.lt_open_file()
		self.lt_wait_preload()
		return self.lt_get_file_url()

	def lt_wait_preload(self):
		if self.is_wait_preload:
			return
		self.is_wait_preload = True
		progress_bar = xbmcgui.DialogProgress()
		progress_bar.create('LTorrentEngine', 'Загрузка ...')
		try:
			while not abortRequested():
				d_stat = self.lt_download_status()
				if d_stat['status'] in ('full_cached', 'cached'):
					break
				elif d_stat['status'] == 'header':
					xbmc.sleep(1000)
					continue
				else:
					complete = float(d_stat['preload_bytes']) / LTORRENT_PRELOAD_BYTES
					if complete > 0.8:
						break
				progress_bar.update(
					int(complete * 100),
					'Загружено %i MB' % (int(d_stat['preload_bytes']) // (1024 ** 2)),
					'Скорость %s Kb/s' % d_stat['speed'],
					'Соединений %s' % d_stat['active_connections']
				)
				if progress_bar.iscanceled():
					self.stop()
					break
				xbmc.sleep(1000)
		finally:
			self.is_wait_preload = False
			progress_bar.close()

	def onPlayBackSeek(self, time, seekOffset):
		xbmc.log('LTorrentClient on playback seek', xbmc.LOGNOTICE)
		self.pause()
		self.lt_wait_preload()
		self.pause()


class xPlayer(xbmc.Player):
	def __init__(self):
		self.tsserv = None
		self.active = True
		self.started = False
		self.ended = False
		self.paused = False
		self.buffering = False
		xbmc.Player.__init__(self)
		width, height = xPlayer.get_skin_resolution()
		w = width
		h = int(0.14 * height)
		x = 0
		y = int((height - h) / 2)
		self._ov_window = xbmcgui.Window(12005)
		self._ov_label = xbmcgui.ControlLabel(x, y, w, h, '', alignment=6)
		self._ov_background = xbmcgui.ControlImage(x, y, w, h, fs_dec(xPlayer.get_ov_image()))
		self._ov_background.setColorDiffuse('0xD0000000')
		self.ov_visible = False
		self.onPlayBackStarted()


	def onPlayBackPaused(self):
		self.ov_show()
		if not xbmc.Player().isPlaying(): xbmc.sleep(2000)
		engine=get_engine()
		status = ''
		while xbmc.Player().isPlaying():
			if self.ov_visible == True:
				try:
					if   engine=="1": status = get_t2h_status()
					elif engine=="6": status = get_ace_status()
					elif engine=="0": status = get_ace_status()
					elif engine=="8": status = get_ts_status()
					elif engine=="10":status = get_ts2_status()
					elif engine=="11":status = get_lt2http_status()
				except: 
					deb_print('== err status ==')
					pass
				self.ov_update(status)
			xbmc.sleep(800)


	def onPlayBackStarted(self):
		self.ov_hide()

	def onPlayBackResumed(self):
		self.ov_hide()
		
	def onPlayBackStopped(self):
		self.ov_hide()
	
	def __del__(self):
		self.ov_hide()

	@staticmethod
	def get_ov_image():
		import base64
		ov_image = fs_enc(os.path.join(addon.getAddonInfo('path'), 'bg.png'))
		if not os.path.isfile(ov_image):
			fl = open(ov_image, 'wb')
			fl.write(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='))
			fl.close()
		return ov_image

	@staticmethod
	def get_skin_resolution():
		import xml.etree.ElementTree as Et
		skin_path = fs_enc(xt('special://skin/'))
		tree = Et.parse(os.path.join(skin_path, 'addon.xml'))
		res = tree.findall('./extension/res')[0]
		return int(res.attrib['width']), int(res.attrib['height'])

	def ov_show(self):
		if not self.ov_visible:
			self._ov_window.addControls([self._ov_background, self._ov_label])
			self.ov_visible = True

	def ov_hide(self):
		if self.ov_visible:
			self._ov_window.removeControls([self._ov_background, self._ov_label])
			self.ov_visible = False

	def ov_update(self, txt=" "):
		if self.ov_visible:
			self._ov_label.setLabel(txt)

def showMessage(heading, message, times = 3000):
	xbmc.executebuiltin('Notification("%s", "%s", %s, "%s")'%(heading, message, times, icon))

def inputbox(t=''):
	skbd = xbmc.Keyboard(t, 'Название:')
	skbd.doModal()
	if skbd.isConfirmed():
		SearchStr = skbd.getText()
		return SearchStr
	else:
		return t

def mfind(t,s,e):
	r=t[t.find(s)+len(s):]
	r2=r[:r.find(e)]
	return r2

def mfindal(http, ss, es):
	L=[]
	while http.find(es)>0:
		s=http.find(ss)
		e=http.find(es, s+len(ss))
		i=http[s:e]
		L.append(i)
		http=http[e+2:]
	return L


try:
	from kodidb import*
except: pass

def abortRequested():
	if sys.version_info.major > 2: return xbmc.Monitor().abortRequested()
	else: return xbmc.abortRequested

def compress(info):
	import base64
	sinfo=repr(info)
	sign=base64.b64encode(sinfo)
	return sign

def decompress(encoded):
	deb_print(encoded)
	import base64
	sinfo=base64.b64decode(encoded)
	deb_print(sinfo)
	return eval(sinfo)


def chek_in():
	try:
		if xbmc.getInfoLabel('ListItem.FileName') == '': FileName = unquote(get_params()['strm'])
		else:                                            FileName = xbmc.getInfoLabel('ListItem.FileName')
		if xbmc.getInfoLabel('ListItem.Path') == '':     Path = __settings__.getSetting("SaveDirectory")#os.path.join(, FileName[:FileName.find('.')])
		else:                                            Path = xbmc.getInfoLabel('ListItem.Path')
		try: 
			FileName = ut(FileName)#.decode('utf-8')
			Path = ut(Path)#.decode('utf-8')
		except: pass
		k_db = KodiDB(FileName, Path, sys.argv[0] + sys.argv[2])
		k_db.PlayerPreProccessing()
		return k_db
	except: 
		return None
	
def chek_out(k_db):
	k_db.PlayerPostProccessing()
	xbmc.sleep(300)
	xbmc.executebuiltin('Container.Refresh')
	xbmc.sleep(200)
	if not xbmc.getCondVisibility('Library.IsScanningVideo'):
		xbmc.executebuiltin('UpdateLibrary("video", "", "false")')


def POST(target, post=None, referer='http://ya.ru'):
	deb_print(target)
	try:
		if sys.version_info.major > 2: post = post.encode()
		req = urllib2.Request(url = target, data = post)
		req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)')
		req.add_header('X-Requested-With', 'XMLHttpRequest')
		if 'json-rpc' in target: req.add_header('content-type', 'application/json')
		resp = urllib2.urlopen(req, timeout=8)
		http = resp.read()
		resp.close()
		return http
	except:
		deb_print('POST ERROR ')
		return ''

def GET(target, XML = False, cache = False, referer=''):
	if __settings__.getSetting('tcache')=='true' and cache: ch = get_ch(target)
	else: ch=''
	if ch!='': return ch
	try:
			req = urllib2.Request(target)
			req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)')
			if XML: req.add_header('X-Requested-With', 'XMLHttpRequest')
			if referer!='': req.add_header('Referer', referer)
			resp = urllib2.urlopen(req, timeout=8)
			r=resp.read()
			r=b2s(r)
			if r!='' and r!=None: add_ch(target, r)
			else: return get_ch(target, True)
			return r
	except:
			deb_print('GET ERROR ')
			ch = get_ch(target, True)
			if ch!='': return ch
			else: return None

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

def open_file():
	dialog = xbmcgui.Dialog()
	fn = dialog.browseSingle(1, 'Открыть', 'files', '.torrent|.magnet')#fs_enc()
	
	if fn!='':
		r = READ(fn)
		'''
		fl = open(fn, "rb")
		#fl = xbmcvfs.File(fn)
		r=fl.read()
		fl.close()
		'''
		if 'magnet:' in repr(r)[:20]:
			magneturi  = r
			if 'dn=' in r: item_name = mfind(r+'&','dn=', '&')
			else: item_name = fn
			fn = ''
		else:
			import bencode, hashlib
			metainfo  = bencode.bdecode(r)
			infohash  = hashlib.sha1(bencode.bencode(metainfo['info'])).hexdigest()
			item_name = rt(metainfo['info']['name'])
			magneturi  = 'magnet:?xt=urn:btih:'+str(infohash)+'&dn='+quote(item_name)
		return {'magnet': magneturi, 'file': fn, 'title': item_name}
	else:
		return {}

def open_strm_old(url, ind=0, purl='', info={}):
	cancel=False
	if purl!='':
		progressBar = xbmcgui.DialogProgress()
		progressBar.create('ТАМ', 'Запуск сохраненного файла')
		for i in range (0,5):
			progressBar.update(20*i, '[COLOR FFFFFF33][B]Нажмите "Отмена" для выбора качества[/B][/COLOR]')
			xbmc.sleep(1600)
			if progressBar.iscanceled():
						progressBar.update(0)
						cancel=True
						break
		progressBar.close()
	if cancel: 
		xbmcplugin.endOfDirectory(handle, False, False)
		xbmc.executebuiltin('ActivateWindow(10025,"'+purl+'", return)')
		xbmc.executebuiltin("Container.Refresh()")
	else:
		play(url, ind)
		pass

def open_strm(url, ind=0, purl='', name=''):
	if purl!='':
		if __settings__.getSetting("SaveMagnet")=='true' and 'magnet' not in url and 'acestream:' not in url: url=t2m(url)
		data={'name':name, 'url':url, 'purl':purl, 'ind':ind}
		__settings__.setSetting("saver_data", repr(data))
		import saver
		break_play=saver.open_strm()
		if break_play == 'false': play(url, ind)
	else:
		play(url, ind)

def save(url, ind=0, purl='', info={}):
	if len(List(url))>1: save_series(url, info, purl)
	else:                save_strm(url, ind, purl, info)

def save_series(url, info={}, purl=''):
		xbmcplugin.endOfDirectory(handle, False, False)
		list=[]
		for i in List(url):
			list.append(i[0])
		if __settings__.getSetting("SaveMagnet")=='true' and 'magnet' not in url and 'acestream:' not in url: url=t2m(url)
		data={'info':info, 'list':list, 'url':url, 'purl':purl}
		__settings__.setSetting("saver_data", repr(data))
		import saver
		saver.main(data)

def save_strm(url, ind=0, purl='', info={}):
		if __settings__.getSetting("SaveMagnet")=='true' and 'magnet' not in url and 'acestream:' not in url: url=t2m(url)
		SaveDirectory = __settings__.getSetting("SaveDirectory")
		if SaveDirectory=="":SaveDirectory=Pdir
		try:    year = int(info['year'])
		except: year = ''
		try:
			name = info['originaltitle'].replace("/"," ").replace("\\"," ").replace("?","").replace(":","").replace('"',"").replace('*',"").replace('|',"")+" ("+str(year)+")"
			title = info['originaltitle']
		except:
			try:    t = info['originaltitle']
			except: t = ''
			title = inputbox(t)
			name = title.replace("/"," ").replace("\\"," ").replace("?","").replace(":","").replace('"',"").replace('*',"").replace('|',"")
		
		uri = sys.argv[0] + '?mode=open_strm'
		uri = uri+ '&url='+quote(url)
		uri = uri+ '&ind='+str(ind)
		if purl!='': uri = uri+ '&purl='+quote(purl)
		if info!={}: uri = uri+ '&name='+quote(title)
		uri = uri+ '&strm='+quote(name+".strm")
		
		fl = open(os.path.join(fs_enc(SaveDirectory),fs_enc(name+".strm")), "w")
		fl.write(uri)
		fl.close()
		
		try: 
			if __settings__.getSetting("SaveNFO")=='true': save_film_nfo(info)
		except:pass
		
		xbmc.executebuiltin('UpdateLibrary("video", "", "false")')

def save_torrent(url, info={}):
		if 'magnet' in url and 'acestream:' not in url: url=m2t(url)
		if 'magnet' in url or 'acestream:' in url: 
			showMessage('TAM', 'Не удалось создать торрент')
			return
		
		SaveDirectory = __settings__.getSetting("SaveDirectory3")
		if SaveDirectory=="":SaveDirectory=Pdir
		try: name = name_bencode(url).replace("/"," ").replace("\\"," ").replace("?","").replace(":","").replace('"',"").replace('*',"").replace('|',"")
		except: name = ''
		if name == '':
			try: name = info['originaltitle'].replace("/"," ").replace("\\"," ").replace("?","").replace(":","").replace('"',"").replace('*',"").replace('|',"")
			except: name = ''
		if name == '':
			try:    t = info['originaltitle']
			except: t = ''
			title = inputbox(t)
			name = title.replace("/"," ").replace("\\"," ").replace("?","").replace(":","").replace('"',"").replace('*',"").replace('|',"")
		
		data = GET(url)
		
		try: fl = open(os.path.join(fs_enc(SaveDirectory),fs_enc(name+".torrent")), "wb")
		except: 
			name=str(time.time())
			fl = open(os.path.join(fs_enc(SaveDirectory),fs_enc(name+".torrent")), "wb")
		fl.write(data)
		fl.close()
		showMessage('Сохранено как', name)


def save_film_nfo(info):
		title=info['title']
		fanart=info['fanart']
		cover=info['cover']
		year=info['year']
		fanarts=[fanart,cover]
		
		try:plot=info['plot']
		except:plot=''
		try:rating=info['rating']
		except:rating=0
		try:originaltitle=info['originaltitle']
		except:originaltitle=title
		
		try:duration=info["duration"]
		except:duration=''
		try:genre=info["genre"].replace(', ', '</genre><genre>')
		except:genre=''
		try:studio=info["studio"]
		except:studio=''
		
		try: director=info["director"]
		except: director=''
		try:cast=info["cast"]
		except:cast=[]
		try: actors=info["actors"]
		except: actors={}
		
		name = info['originaltitle'].replace("/"," ").replace("\\"," ").replace("?","").replace(":","").replace('"',"").replace('*',"").replace('|',"")+" ("+str(info['year'])+")"
		cn=name.find(" (")
		
		SaveDirectory = __settings__.getSetting("SaveDirectory")
		if SaveDirectory=="":SaveDirectory=Pdir
		
		nfo='<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'+chr(10)
		nfo+='<movie>'+chr(10)
		
		nfo+="	<title>"+title+"</title>"+chr(10)
		nfo+="	<originaltitle>"+originaltitle+"</originaltitle>"+chr(10)
		nfo+="	<genre>"+genre+"</genre>"+chr(10)
		nfo+="	<studio>"+studio+"</studio>"+chr(10)
		nfo+="	<director>"+director+"</director>"+chr(10)
		nfo+="	<year>"+str(year)+"</year>"+chr(10)
		nfo+="	<plot>"+plot+"</plot>"+chr(10)
		nfo+='	<rating>'+str(rating)+'</rating>'+chr(10)
		nfo+='	<runtime>'+duration+' min.</runtime>'+chr(10)
		
		nfo+="	<fanart>"+chr(10)
		for fan in fanarts:
			nfo+="		<thumb>"+fan+"</thumb>"+chr(10)
		nfo+="		<thumb>"+cover+"</thumb>"+chr(10)
		nfo+="	</fanart>"+chr(10)
		
		nfo+="	<thumb>"+cover+"</thumb>"+chr(10)
		
		for actor in cast:
			nfo+="	<actor>"+chr(10)
			nfo+="		<name>"+actor+"</name>"+chr(10)
			nfo+="	</actor>"+chr(10)
		
		nfo+="</movie>"+chr(10)
		
		fl = open(os.path.join(fs_enc(SaveDirectory),fs_enc(name+".nfo")), "w")
		fl.write(nfo)
		fl.close()

def t2m(url):
	deb_print('--- t2m ---')
	try:
		import bencode, hashlib
		if url.startswith('http') or 'file:' in url: r = GET(url, cache = True)
		else: 								r = READ(url)
		metainfo = bencode.bdecode(r)
		announce=''
		if 'announce' in metainfo.keys(): announce='&tr='+quote(metainfo['announce'])
		if 'announce-list' in metainfo.keys():
			try:
				for ans in metainfo['announce-list']:
					announce=announce+'&tr='+quote(ans[0])
			except:
				pass
		infohash = hashlib.sha1(bencode.bencode(metainfo['info'])).hexdigest()
		magneturi  = 'magnet:?xt=urn:btih:'+str(infohash)+'&dn='+quote(rt(metainfo['info']['name']))+announce
		return magneturi
	except:
		if '/itorrents.org/' in url: 
			infohash = mfind(url, '/torrent/','.torrent')
			if len(infohash)>30: return 'magnet:?xt=urn:btih:'+str(infohash)+'&dn='+str(infohash)
		return url

def m2t(url):
	deb_print('--- m2t ---')
	if 'btih:' in url:
		try:
			CID=mfind(url+'&', 'btih:', '&')
			t_url='https://t.torrage.info/download?h='+CID
			r=GET(t_url, referer='https://torrage.info/', cache = True)
			if 'd8:' in r or 'd7:' in r or ':announc' in r: return t_url
			
			t_url='http://127.0.0.1:8095/proxy/http://itorrents.org/torrent/'+CID+'.torrent'
			r=GET(t_url, cache = True)
			if 'd8:' in r or 'd7:' in r or ':announc' in r: return t_url
			
			t_url='http://127.0.0.1:8095/proxy/https://krasfs.ru/download.php?hash='+CID
			r=GET(t_url, cache = True)
			if 'd8:' in r or 'd7:' in r or ':announc' in r: return t_url
			
		except: pass
	return url

#print (m2t('magnet:?xt=urn:btih:9eda4ca7c668fc9e010c1dd093727832b00dd3de&dn=rutor.info&tr=udp://opentor.org:2710&tr=udp://opentor.org:2710&tr=http://retracker.local/announce'))
def lt2http_set(post):
	lt2h_host = __settings__.getSetting("lt_serv")
	lt2h_port = __settings__.getSetting("lt_port")
	host = 'http://'+lt2h_host+':'+str(lt2h_port)
	POST(host+'/settings/set', post)

def get_fid(url, ind):
	L=List(url)
	Lt=[]
	Li=[]
	try:
		for i in L:
			Lt.append(i[0])
			Li.append(i[0])
		Lt.sort()
		t=Li[int(ind)]
		n=0
		for i in Lt:
			if i == t: return n
			n+=1
	except: pass
	return 0

def media(t):
	L = ['.avi', '.mov', '.mp4', '.mpg', '.mpeg', '.m4v', '.mkv', '.ts', '.vob', '.wmv', '.m2ts']
	for i in L:
		if i in t.lower(): return True
	return False

def get_eid(url, ind):
	L=List(url)
	Lt=[]
	Li=[]
	for i in L:
		if media(i[0]): Lt.append(i[0])
		Li.append(i[0])
	Lt.sort()
	t=Li[int(ind)]
	n=0
	for i in Lt:
		if i == t: return n
		n+=1
	return 0

def get_time():
	try:
		tm = xbmc.Player().getTime()
		if tm < 0 or tm == None: tm = 0
	except:
		tm = 0
	return 0

def InstallAddon(an):
	try: 
		xbmcaddon.Addon(an)
	except: 
		showMessage('Установка модуля', an)
		#xbmc.executebuiltin('InstallAddon("'+an+'")')
		xbmc.executebuiltin('RunPlugin("plugin://'+an+'")')


def get_engine():
	global engine
	if engine!='':
		de={'ace':'0', 't2http':'1', 'yatp':'2', 'torrenter':'3', 'elementum':'4', 'xbmctorrent':'5', 'ace_proxy':'6', 'quasar':'7', 'torr_server':'8', 'torrserver':'8', 'torrserver_tam':'10', 'lt2http':'11'}
		try:    tengine=de[engine]
		except: tengine= __settings__.getSetting("Engine")
	if engine=='': 
				tengine=__settings__.getSetting("Engine")
	return tengine


def skip_ad():
		deb_print('==NoAD==')
		Player=xbmc.Player()
		for t in range(100):
			xbmc.sleep(500)
			if xbmc.Player().isPlaying():
				deb_print('==NoAD isPlaying==')
				break
		
		deb_print('==NoAD PlFile==')
		for t in range(50):
			xbmc.sleep(500)
			try: PlFile=Player.getPlayingFile()
			except: PlFile=''
			try: PlTime=Player.getTime()
			except: PlTime=0
			deb_print('PlFile '+PlFile)
			if PlFile!='' and PlTime>0 and PlTime<150:
				xbmc.sleep(500)
				deb_print('==NoAD seekTime==')
				Player.seekTime(35)
				break


def play(url, ind=0, ad=0):
	deb_print('TAM play: '+url)
	k_db=chek_in()
	engine=get_engine()
	
	if ad!=0: xbmc.executebuiltin('RunPlugin("plugin://plugin.video.tam/?mode=skip_ad")')
	
	if 'magnet:' in url:
		if   engine=="0": play_ace_proxy(url, ind)
		elif engine=="1": play_t2h (url, ind)
		elif engine=="2": play_yatp(url, ind)
		elif engine=="3": play_torrenter(url, ind)
		elif engine=="4": play_elementum(url, ind)
		elif engine=="5": play_xbmctorrent(url, ind)
		elif engine=="6": play_ace_proxy(url, ind)
		elif engine=="7": play_quasar(url, ind)
		elif engine=="8": play_torr_server(url, ind)
		elif engine=="10":play_torr_server_tam(url, ind)
		elif engine=="11":play_lt2http(url, ind)
		else:             play_t2h (url, ind)
	
	elif 'acestream:' in url:
						  play_ace_proxy(url, ind)
	
	elif 'file:' in url or url.startswith('http'):
		if engine=="0": play_ace (url, ind)
		if engine=="1": play_t2h (url, ind)
		if engine=="2": play_yatp(url, ind)
		if engine=="3": play_torrenter(url, ind)
		if engine=="4": play_elementum(url, ind)
		if engine=="5": play_xbmctorrent(url, ind)
		if engine=="6": play_ace_proxy(url, ind)
		if engine=="7": play_quasar(url, ind)
		if engine=="8": play_torr_server(url, ind)
		if engine=="9": play_ltorrent(url, ind)
		if engine=="10":play_torr_server_tam(url, ind)
		if engine=="11":play_lt2http(url, ind)
	
	else:
		if engine=="0": play_ace (f2u(url), ind)
		if engine=="1": play_t2h (f2u(url), ind)
		if engine=="2": play_yatp(url, ind)
		if engine=="3": play_torrenter(f2u(url), ind)
		if engine=="4": play_elementum(url, ind)
		if engine=="5": play_xbmctorrent(url, ind)
		if engine=="6": play_ace_proxy(f2u(url), ind)
		if engine=="7": play_quasar(url, ind)
		if engine=="8": play_torr_server(url, ind)
		if engine=="9": play_ltorrent(url, ind)
		if engine=="10":play_torr_server_tam(url, ind)
		if engine=="11":play_lt2http(url, ind)
	
	if __settings__.getSetting('ToggleWatched')=='true': xbmc.executebuiltin('Action("ToggleWatched")')
	if k_db != None: chek_out(k_db)



def play_lt2http(url, ind):
	if __settings__.getSetting("lt_api")=='0':  
		play_lt2http_mod(url, ind)
	else: 
		try: play_lt2http_tam(url, ind)
		except: 
			xbmc.sleep(1000)
			play_lt2http_tam(url, ind)

def play_lt2http_tam(url, ind):
	progressBar = xbmcgui.DialogProgress()
	progressBar.create('lt2http', 'Запуск')
	
	lt2h_host = __settings__.getSetting("lt_serv")
	lt2h_port = __settings__.getSetting("lt_port")
	host = 'http://'+lt2h_host+':'+str(lt2h_port)
	try: mem = int(__settings__.getSetting("lt_memory_size"))
	except: mem = 0
	try: buf = int(__settings__.getSetting("lt_buffer_size"))
	except: buf = 0
	setstr=''
	if mem > 0: 
		memsz = str(mem*50)
		setstr+='"auto_memory_size":false, "memory_size":'+memsz
	else:
		setstr+='"auto_memory_size":true'
	
	if buf > 0: 
		bufz = str(buf*20)
		bufe = str(buf*4)
		setstr+=', "buffer_size":'+bufz+', "end_buffer_size":'+bufe
	
	lt2http_set('{'+setstr+'}')
	
	if 'magnet' not in url: m_url=t2m(url)
	else: m_url=url
	hash=mfind(m_url+'&', 'btih:', '&')
	
	false=False
	true=True
	null=None
	
	try: L=eval(GET(host+'/torrents', True))
	except: 
		progressBar.update(0, 'Ошибка соединения')
		xbmc.sleep(1000)
		progressBar.close()
		return

	in_list = False
	for t in L:
		if hash == str(t['hash']):
			in_list = True
			break
	
	if not in_list: 
		GET(host+'/service/add/uri?uri='+quote(url), True)
		for i in range (15):
			xbmc.sleep(1000)
			L=eval(GET(host+'/torrents', True))
			for t in L:
				if hash == str(t['hash']): 
					in_list = True
					break
			if in_list: break
	
	uri = ''
	if in_list:
		global LT2HASH
		LT2HASH = hash
		for n in range (4):
			filesList=eval(GET(host+'/torrents/'+hash+'/files', True))
			for i in filesList:
				if i['id'] == int(ind): 
					uri = i['stream'].replace('\\/','/')
					break
			if uri != '': break
			progressBar.update(0, 'Получение потока: '+str(n))
			xbmc.sleep(2000)
	
	if uri == '':
		progressBar.update(0, 'Ошибка открытия')
		xbmc.sleep(1000)
		progressBar.close()
		return
	
	plb = False
	seeds=0
	progress=0
	download=0
	urllib2.urlopen(uri, timeout=1)
	for n in range(120):
		xbmc.sleep(1000)
		try:i = eval(GET(host+'/torrents/'+hash+'/status', True))
		except: pass
		try: seeds=i["seeders"]
		except: pass
		try: speed=int(i["download_rate"]/1024)
		except: pass
		try: progress=int(i["progress"]*100)
		except: progress=0
		try: download=int(i["total_download"]/1024/1024)
		except: pass
		
		try:progressBar.update(int(progress*10), xt('Предварительная буферизация: '+str(download)+" MB"), "Сиды: "+str(seeds), "Скорость: "+str(speed)+' Kbit/s')
		except:progressBar.update(int(progress*10), xt('Предварительная буферизация: '+str(download)+" MB \nСиды: "+str(seeds)+" \nСкорость: "+str(speed)+' Kbit/s'))
		
		if progressBar.iscanceled() or abortRequested():
				progressBar.update(0)
				progressBar.close()
				clear_lt2http()
				return
		
		if progress>12 or (download>150 and n>1 and speed > 200):
			plb = True
			break
	
	progressBar.update(0)
	progressBar.close()
	
	if plb:
		Player=xPlayer()
		item = xbmcgui.ListItem(path=uri)
		xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
	else:
		clear_lt2http()
		return
	
	for i in range(30):
			xbmc.sleep(1000)
			if xbmc.Player().isPlaying() and get_time()>0: break
	n=0
	while not abortRequested() and xbmc.Player().isPlaying():
		xbmc.sleep(500)
		n+=1
		if n>10:
			lt2h.getStreamUri(hash, ind)
			n=0
	clear_lt2http()

def play_lt2http_mod(url, ind):
	lt2h.Play(url, ind, xplayer=xPlayer())
	return


def play_torr_server(url, ind):
	if __settings__.getSetting("ts_api")=='0':  
		play_torr_server_mod(url, ind)
	else: 
		play_torr_server_tam(url, ind)

def play_torr_server_mod(url, ind):
	global engine_ts
	global index_ts
	index_ts = get_fid(url, ind)#int(ind)
	if 'magnet' not in url: url=t2m(url)
	
	InstallAddon('script.module.torrserver')
	try:
		import torrserve_stream
		tss = torrserve_stream.Settings()
		engine_ts =  torrserve_stream.Engine(uri=url, host=tss.host, port=tss.port)
		if __settings__.getSetting('ts_info')== 'true': Player=xPlayer()
		player = torrserve_stream.Player(uri=url, sort_index=index_ts)
	except:
		deb_print('error torrserve_stream')

def play_torr_server_tam_old(url, ind):
	deb_print('-=-=-=-= play_torr_server =-=-=-=-')
	host=str(__settings__.getSetting("ts_serv"))
	port=str(__settings__.getSetting("ts_port"))
	
	fid = get_fid(url, ind)
	__settings__.setSetting("ts_FID", str(fid))
	
	if 'magnet' not in url: url=t2m(url)
	CID = ''
	if 'btih:' in url:
		if '&' not in url: url=url+'&'
		CID=mfind(url+'&', 'btih:', '&')
	__settings__.setSetting("ts_CID", CID)
	
	progressBar = xbmcgui.DialogProgress()
	progressBar.create('TorrServ', 'Запуск')
	try:progressBar.update(0, 'TorrServ', 'Загрузка', "")
	except:progressBar.update(0, 'Загрузка')
	uri1='http://'+host+':'+port+'/torrent/add'
	post = '{"Link":"'+url+'","DontSave":false}'
	json = POST(uri1, post)
	deb_print(json)
	
	try:progressBar.update(0, 'TorrServ', 'Буферизация', "")
	except:progressBar.update(0, 'Буферизация')
	for i in range (100):
		if progressBar.iscanceled() or abortRequested():
				progressBar.update(0)
				progressBar.close()
				return
		try:
			uri  = 'http://'+host+':'+port+'/torrent/stat'
			post = '{"Hash":"'+CID+'"}'
			json = POST(uri, post)
			deb_print(json)
			false=False
			true=True
			null=None
			j=eval(json)
			status = j["TorrentStatus"]
			peers = j["TotalPeers"]
			seeders = j["ConnectedSeeders"]
			load = j["BytesWritten"]
			
			if   status == 0: st_status='Поиск'
			elif status == 1: st_status='Буферизация'
			elif status == 3: st_status='Воспроизведение'
			else:             st_status = str(status)
			deb_print(status)
			try: progressBar.update(int(i*3), st_status, 'Загружено: '+str(int(load/256))+'Мб', 'Сиды: '+str(seeders)+' Пиры:'+str(peers))
			except: progressBar.update(int(i*3), st_status+'\nЗагружено: '+str(int(load/256))+'Мб \nСиды: '+str(seeders)+' Пиры:'+str(peers))
			if status == 3: break
		except: pass
		xbmc.sleep(300)
	
	progressBar.update(100, 'Воспроизведение')
	
	Player=xPlayer()
	uri='http://'+host+':'+port+'/torrent/play?link='+ quote(url)+"&file="+str(fid)
	item = xbmcgui.ListItem(path=uri)
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
	
	progressBar.close()
	
	for i in range(30):
			xbmc.sleep(1000)
			if xbmc.Player().isPlaying() and get_time()>0: break
	
	while not abortRequested() and xbmc.Player().isPlaying():
		xbmc.sleep(500)

def play_torr_server_tam(url, ind):
	deb_print('-=-=-=-= play_torr_server =-=-=-=-')
	
	host=str(__settings__.getSetting("ts_serv"))
	port=str(__settings__.getSetting("ts_port"))
	save_to_db=str(__settings__.getSetting("ts_save"))
	
	ver = GET('http://'+host+':'+port+'/echo')
	__settings__.setSetting("ts_VER", ver)
	#print(ver)
	if 'MatriX' not in ver: return play_torr_server_tam_old(url, ind)
	
	progressBar = xbmcgui.DialogProgress()
	progressBar.create('TorrServ', 'Запуск')
	
	fid = get_fid(url, ind)+1#ind
	__settings__.setSetting("ts_FID", str(fid))
	
	murl=url
	if 'magnet' not in url: murl=t2m(url)
	CID = ''
	if 'btih:' in murl: CID=mfind(murl+'&', 'btih:', '&')
	__settings__.setSetting("ts_CID", CID)
	if not url.startswith('http'): url=file2url(url)#murl
	
	
	progressBar.update(0, 'Загрузка')
	uri1='http://'+host+':'+port+'/torrents'
	post = '{"action":"add","link":"'+url+'","save_to_db":'+save_to_db+'}'
	json = POST(uri1, post)
	if json=='': json = POST(uri1, '{"action":"add","link":"'+CID+'","save_to_db":'+save_to_db+'}')
	#deb_print(json)
	
	if json=='': 
		progressBar.update(0, 'Ошибка открытия торрента')
		time.sleep(1)
		progressBar.update(0)
		progressBar.close()
		return
	#m3u = GET('http://'+host+':'+port+'/stream/fname?link='+url+'&index='+str(ind)+'&m3u')
	progressBar.update(0, 'Буферизация')
	try:
		preload_uri  = 'http://'+host+':'+port+'/stream/fname?link='+CID+'&index='+str(fid)+'&preload'
		req = urllib2.Request(preload_uri)
		resp = urllib2.urlopen(req, timeout=0.3)
		data=self.resp.read(128)
	except: pass
	err=0
	for i in range (100):
		if progressBar.iscanceled() or abortRequested():
				progressBar.update(0)
				progressBar.close()
				return
		try:
			false=False
			true=True
			null=None
			
			uri  = 'http://'+host+':'+port+'/stream/fname?link='+CID+'&index='+str(fid)+'&stat'
			json = GET(uri)
			#deb_print(json)
			j=eval(json)
			#deb_print(j.keys())
			try: status = j["stat"]
			except: status = 0
			try: peers = j["total_peers"]
			except: peers = 0
			try: seeders = j["connected_seeders"]
			except: seeders = 0
			try: preload_size = j['preload_size']
			except: preload_size = 32*1024*1024
			try: load = j['preloaded_bytes']
			except: load = 0
			try: speed = j['download_speed']*8
			except: speed = 0
			if   status == 0: st_status='Поиск'
			elif status == 1: st_status='Поиск'
			elif status == 3: st_status='Буферизация'
			else:             st_status = str(status)#j['stat_string']
			#deb_print(str(status)+' speed: '+str(int(speed/1024))+' download: '+str(int(load/1024/1024))+' / '+str(int(preload_size/1024/1024))+' MB seeders: '+str(seeders)+' peers:'+str(peers))
			try:    progressBar.update(int(load*100/preload_size), st_status,  'Скорость: '+str(int(speed/1024))+' кбит/c   Загружено: '+str(int(load/1024/1024))+' Мб', 'Сиды: '+str(seeders)+'  Пиры: '+str(peers))
			except: progressBar.update(int(load*100/preload_size), st_status+'\nСкорость: '+str(int(speed/1024))+' кбит/c   Загружено: '+str(int(load/1024/1024))+' Мб \nСиды: '+str(seeders)+'  Пиры: '+str(peers))
			if status == 3 and load>=preload_size: break
			err=0
		except:
			err+=1
			if err>1: progressBar.update(i*30, 'Ошибка торрента')
			if err>2:
				progressBar.update(0)
				progressBar.close()
				return
		time.sleep(1)
		#xbmc.sleep(300)
	
	progressBar.update(100, 'Воспроизведение')
	
	Player=xPlayer()
	#uri='http://'+host+':'+port+'/torrent/play?link='+ quote(url)+"&file="+str(fid)
	uri='http://'+host+':'+port+'/stream/?link='+CID+'&index='+str(fid)+'&play'
	
	item = xbmcgui.ListItem(path=uri)
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
	
	progressBar.close()
	
	for i in range(30):
			xbmc.sleep(1000)
			if xbmc.Player().isPlaying() and get_time()>0: break
	
	while not abortRequested() and xbmc.Player().isPlaying():
		xbmc.sleep(500)

def play_ace(url, ep=0, id='0'):
	if __settings__.getSetting("ace_api")=='0':
		play_ace_engine(url, ep, id)
	else: 
		play_ace_proxy(url, ep, id)

def play_ace_engine(url, ep=0, id='0'):
	InstallAddon('script.module.torrent.ts')
	torr_link = url
	ind = ep
	try:
		from TSCore import TSengine as tsengine
		TSplayer=tsengine()
		if 'magnet' in torr_link: 			out=TSplayer.load_torrent(CID,'INFOHASH')
		elif 'acestream:' in torr_link: 	out=TSplayer.load_torrent(CID,'PID')
		else: 								out=TSplayer.load_torrent(torr_link,'TORRENT')
		
		if 'magnet' not in url and 'acestream:' not in url: url=t2m(url)
		title=url
		cover=''
		try:ACE_start()
		except: pass
		progressBar = xbmcgui.DialogProgress()
		progressBar.create('ACE Stream', 'Запуск')
		srv=__settings__.getSetting("p2p_serv")#'127.0.0.1'
		prt=__settings__.getSetting("p2p_port")#'6878'
		if 'btih:' in url:
			CID=mfind(url+'&', 'btih:', '&')
			as_url='http://'+srv+':'+prt+'/ace/getstream?infohash='+CID+"&format=json&_idx="+str(ep)
		elif 'acestream:' in url:
			CID=url.replace('acestream://','')
			as_url='http://'+srv+':'+prt+'/ace/getstream?id='+CID+"&format=json&_idx="+str(ep)
		else:
			as_url='http://'+srv+':'+prt+'/ace/getstream?url='+url+"&format=json&_idx="+str(ep)
		
		if as_url!='':
			try: json=eval(GET(as_url).replace('null','"null"'))["response"]
			except: 
				xbmc.sleep(1000)
				try: json=eval(GET(as_url).replace('null','"null"'))["response"]
				except: 
					progressBar.update(0, 'Ошибка открытия')
					xbmc.sleep(1000)
					progressBar.close()
					return
			
			deb_print(json)
			try: progressBar.update(0, 'ACE Stream', 'Контент найден', "")
			except: progressBar.update(0, 'Контент найден')
			stat_url=json["stat_url"]
			stop_url=json["command_url"]+'?method=stop'
			purl=json["playback_url"]
			
			__settings__.setSetting("stat_url", stat_url)
			try: progressBar.update(0, 'ACE Stream', 'Подключение', "")
			except: progressBar.update(0, 'Подключение')
			while not abortRequested():
				j=eval(GET(stat_url).replace('null','"null"'))["response"]
				if j=={}:
					pass
					progressBar.update(0, 'Ожидание')
				else:
					try:
						status=j['status']
						if status=='dl': break
						download=j['downloaded']
						progress=j['total_progress']
						if progress>10: progress = 10
						seeds=j['peers']
						speed=j['speed_down']
						try: progressBar.update(progress*10, xt('Предварительная буферизация: '+str(download/1024/1024)+" MB"), "Сиды: "+str(seeds), "Скорость: "+str(speed)+' Kbit/s')
						except:progressBar.update(progress*10, xt('Предварительная буферизация: '+str(int(download/1024/1024))+" MB \nСиды: "+str(seeds)+" \nСкорость: "+str(speed)+' Kbit/s'))
					except: pass
				xbmc.sleep(500)
				if progressBar.iscanceled() or abortRequested():
					progressBar.update(0)
					progressBar.close()
					GET(stop_url)
					return
			
			progressBar.close()
		print(ind)
		title=get_item_name(torr_link, ind)
		if out=='Ok': TSplayer.play_url_ind(int(ind),title, icon, icon, True)
		TSplayer.end()
		
		if out==False: play_ace_proxy(torr_link, ind)
		xbmc.executebuiltin("Container.Refresh")
		return out
	except: 
		play_ace_proxy(torr_link, ind)
		return '0'


def play_ace_proxy(url, ep=0, id='0'):
	false=False
	true=True
	null=None
	
	if 'magnet' not in url and 'acestream:' not in url: url=t2m(url)
	title=url
	cover=''
	ACE_start()
	try:ACE_start()
	except: pass
	progressBar = xbmcgui.DialogProgress()
	progressBar.create('ACE Stream', 'Запуск')
	srv=__settings__.getSetting("p2p_serv")#'127.0.0.1'
	prt=__settings__.getSetting("p2p_port")#'6878'
	if 'btih:' in url:
		CID=mfind(url+'&', 'btih:', '&')
		as_url='http://'+srv+':'+prt+'/ace/getstream?infohash='+CID+"&format=json&_idx="+str(ep)
	elif 'acestream:' in url:
		CID=url.replace('acestream://','')
		as_url='http://'+srv+':'+prt+'/ace/getstream?id='+CID+"&format=json&_idx="+str(ep)
	else:
		as_url='http://'+srv+':'+prt+'/ace/getstream?url='+url+"&format=json&_idx="+str(ep)
	
	if __settings__.getSetting("p2p_dlnk") == 'true':
		xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=as_url.replace("&format=json", "")))
		return
	
	deb_print(as_url)
	if as_url!='':
		try: 
			r=GET(as_url)
			deb_print(r)
			json=eval(r.replace('null','"null"'))["response"]
		except: 
			xbmc.sleep(1000)
			try: json=eval(GET(as_url).replace('null','"null"'))["response"]
			except: 
				progressBar.update(0, 'Ошибка открытия')
				xbmc.sleep(1000)
				progressBar.close()
				return
		
		deb_print(json)
		try:progressBar.update(0, 'ACE Stream', 'Контент найден', "")
		except:progressBar.update(0, 'Контент найден')
		stat_url=json["stat_url"]
		stop_url=json["command_url"]+'?method=stop'
		purl=json["playback_url"]
		
		__settings__.setSetting("stat_url", stat_url)
		try:progressBar.update(0, 'ACE Stream', 'Подключение', "")
		except:progressBar.update(0, 'Подключение')
		while not abortRequested():
			j=eval(GET(stat_url).replace('null','"null"'))["response"]
			if j=={}:
				pass
				try: progressBar.update(0, 'ACE Stream', 'Ожидание', "")
				except: progressBar.update(0, 'Ожидание')
			else:
				try:
					status=j['status']
					if status=='dl': break
					download=j['downloaded']
					progress=j['total_progress']
					if progress>10: progress = 10
					seeds=j['peers']
					speed=j['speed_down']
					try:progressBar.update(progress*10, xt('Предварительная буферизация: '+str(int(download/1024/1024))+" MB"), "Сиды: "+str(seeds), "Скорость: "+str(speed)+' Kbit/s')
					except:progressBar.update(progress*10, xt('Предварительная буферизация: '+str(int(download/1024/1024))+" MB \nСиды: "+str(seeds)+" \nСкорость: "+str(speed)+' Kbit/s'))
				except: pass
			xbmc.sleep(500)
			if progressBar.iscanceled() or abortRequested():
				progressBar.update(0)
				progressBar.close()
				GET(stop_url)
				return
		try: progressBar.update(0, 'ACE Stream', 'Буферизация закончена', '')
		except: progressBar.update(100, 'Буферизация закончена')
		
		#GET(stat_url)
		deb_print(purl)
		
		if __settings__.getSetting("ace_dl_end")=='true':
			murl = as_url.replace('getstream?','manifest.m3u8?').replace('&format=json','')
			deb_print(murl)
			m3u8 = GET(murl)
			ch_list = []
			if m3u8 == None:
				xbmc.sleep(2000)
				m3u8 = GET(murl)
			
			try:
				for i in m3u8.splitlines():
					if '/ace/c/' in i: ch_list.append(i)
				try: progressBar.update(0, 'ACE Stream', 'Проверка', '')
				except: progressBar.update(0, 'Проверка')
				try: 
					response = urllib2.urlopen(ch_list[-1], timeout=5)
					data=response.read(1*1024*1024)
				except: deb_print('-err ch[-1]-')
				try: 
					response = urllib2.urlopen(ch_list[0], timeout=5)
					data=response.read(128)
				except: deb_print('-err ch[0]-')
			except:
				deb_print('-err load m3u8-')
		
		
		try: item = xbmcgui.ListItem(path=purl, iconImage=cover, thumbnailImage=cover)
		except: item = xbmcgui.ListItem(path=purl)
		try: item.setArt({ 'poster': cover, 'fanart' : fanart, 'thumb': cover, 'icon': cover})
		except: pass
		try: item.setProperty('fanart_image', fanart)
		except: pass
			
		try: progressBar.update(0, 'ACE Stream', 'Воспроизведение', '')
		except: progressBar.update(0, 'Воспроизведение')
		
		xbmc.sleep(500)
		xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
		progressBar.update(0)
		progressBar.close()
		
		for i in range(30):
			xbmc.sleep(1000)
			if xbmc.Player().isPlaying() or abortRequested(): break
		
		Player=xPlayer()
		while not abortRequested() and xbmc.Player().isPlaying():
					xbmc.sleep(500)
		GET(stop_url)
	else:
		showMessage('TAM','Поток не найден')


def play_t2h(uri, file_id=0):
	global engine_t2h
	#if 'magnet' not in uri: uri=t2m(uri)
	InstallAddon('script.module.torrent2http')
	#if True:
	try:
		resume=None
		DDir=__settings__.getSetting("DownloadDirectory")
		if DDir=="": DDir=os.path.join(xt("special://home/"),"userdata")
		if __settings__.getSetting("keepfile")=='true': 
			keepfile = True
			crc = CRC32(uri)
			resume=os.path.join(DDir, crc+'.resume')
		else: 
			keepfile = False
		sys.path.append(os.path.join(xt("special://home/"),"addons","script.module.torrent2http","lib"))
		from torrent2http import State, Engine, MediaType
		progressBar = xbmcgui.DialogProgress()
		from contextlib import closing
		progressBar.create('Torrent2Http', 'Запуск')
		ready = False
		pre_buffer_bytes = 15*1024*1024 # Set pre-buffer size to 15Mb. This is a size of file that need to be downloaded before we resolve URL to XMBC 
		
		if keepfile:
			engine = Engine(uri, download_path=DDir, enable_dht=True, dht_routers=["router.bittorrent.com:6881","router.utorrent.com:6881"], user_agent = 'uTorrent/2200(24683)', keep_complete=keepfile, keep_files=keepfile, resume_file=resume)
		else: 
			engine = Engine(uri, download_path=DDir, enable_dht=True, dht_routers=["router.bittorrent.com:6881","router.utorrent.com:6881"], user_agent = 'uTorrent/2200(24683)')
		
		engine_t2h = engine
		with closing(engine):
			# Start engine and instruct torrent2http to begin download first file, 
			# so it can start searching and connecting to peers  
			engine.start(file_id)
			try:progressBar.update(0, 'Torrent2Http', 'Загрузка торрента', "")
			except:progressBar.update(0, 'Загрузка торрента')
			while not abortRequested() and not ready:
				xbmc.sleep(500)
				status = engine.status()
				# Check if there is loading torrent error and raise exception 
				engine.check_torrent_error(status)
				# Trying to detect file_id
				
				if file_id is None:
					if abortRequested(): break
					# Get torrent files list, filtered by video file type only
					files = engine.list(media_types=[MediaType.VIDEO])
					# If torrent metadata is not loaded yet then continue
					if files is None:
						continue
					# Torrent has no video files
					if not files:
						break
						progressBar.close()
					# Select first matching file
					file_id = files[0].index
					file_status = files[0]
				else:
					# If we've got file_id already, get file status
					try: file_status = engine.file_status(file_id)
					except: file_status = engine.file_status(0)
					# If torrent metadata is not loaded yet then continue
					
					if not file_status:
						if progressBar.iscanceled(): break
						continue
						#break
				
				if status.state == State.DOWNLOADING:
					# Wait until minimum pre_buffer_bytes downloaded before we resolve URL to XBMC
					if file_status.download >= pre_buffer_bytes:
						ready = True
						break
					#downloadedSize = status.total_download / 1024 / 1024
					getDownloadRate = status.download_rate / 1024 * 8
					#getUploadRate = status.upload_rate / 1024 * 8
					getSeeds = status.num_seeds
					
					try: progressBar.update(100*file_status.download/pre_buffer_bytes, xt('Предварительная буферизация: '+str(file_status.download/1024/1024)+" MB"), "Сиды: "+str(getSeeds), "Скорость: "+str(getDownloadRate)[:4]+' Mbit/s')
					except: progressBar.update(int(100*file_status.download/pre_buffer_bytes), 'Буферизация: '+str(int(file_status.download/1024/1024))+" MB \n Сиды: "+str(getSeeds)+"\n Скорость: "+str(getDownloadRate)[:4]+' Mbit/s')
				elif status.state in [State.FINISHED, State.SEEDING]:
					#progressBar.update(0, 'T2Http', 'We have already downloaded file', "")
					# We have already downloaded file
					ready = True
					break
				
				if progressBar.iscanceled():
					progressBar.update(0)
					progressBar.close()
					break
				# Here you can update pre-buffer progress dialog, for example.
				# Note that State.CHECKING also need waiting until fully finished, so it better to use resume_file option
				# for engine to avoid CHECKING state if possible.
				# ...
			progressBar.update(0)
			progressBar.close()
			if ready:
				# Resolve URL to XBMC
				Player=xPlayer()
				item = xbmcgui.ListItem(path=file_status.url)
				xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
				if __settings__.getSetting("t2h_play") == '1':
					playlist = xbmc.PlayList (xbmc.PLAYLIST_VIDEO)
					playlist.clear()
					playlist.add(url=file_status.url, listitem=item)
					xbmc.Player().play(playlist)
				xbmc.sleep(3000)
				#xbmc.Player().Play(item)
				xbmc.sleep(3000)
				# Wait until playing finished or abort requested
				while not abortRequested() and xbmc.Player().isPlaying():
					xbmc.sleep(500)
	except: pass



def play_yatp(url, ind):
	purl ="plugin://plugin.video.yatp/?action=play&torrent="+ quote(url)+"&file_index="+str(ind)
	item = xbmcgui.ListItem(path=purl)
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

def play_torrenter(url, ind):
	purl ="plugin://plugin.video.torrenter/?action=playSTRM&url="+ quote(url)+"&file_index="+str(ind)+"&index="+str(ind)
	item = xbmcgui.ListItem(path=purl)
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

def play_elementum(url, ind):
	try:    el_ver = eval(xbmc.getInfoLabel("System.AddonVersion(plugin.video.elementum)").replace(".",","))
	except: el_ver = (0, 0, 0)
	if el_ver >= (0, 1, 52): 
		index = "&oindex="+str(ind)
	else: 
		eid = get_eid(url, ind)
		index = "&index="+str(eid)
	
	purl ="plugin://plugin.video.elementum/play?uri="+ quote(url)+index
	item = xbmcgui.ListItem(path=purl)
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

def play_quasar(url, ind):
	purl = "plugin://plugin.video.quasar/play?uri=" + quote(url)+"&index="+str(ind)
	item = xbmcgui.ListItem(path=purl)
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)



def play_xbmctorrent(url, ind):
	purl ="plugin://plugin.video.xbmctorrent/play/"+ quote(url)+"/"+str(ind)
	item = xbmcgui.ListItem(path=purl)
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

def play_ltorrent_off(url, ind):
	false=False
	true=True
	if url.startswith('http'): post = '{"action":"open_torrent", "url":"'+url+'"}'
	else:                      post = '{"action":"open_torrent", "file":"'+url+'"}'
	#post = '{"action":"open_torrent", "url":"http://td-soft.narod.ru/suits.torrent"}'
	rec = POST('http://localhost:8888/api', post)
	if rec!='':
		info_hash = eval(rec)['info_hash']
		#post = '{"action":"get_file_list"}'
		purl = 'http://localhost:8888/play/'+info_hash+'/'+str(ind)+'/'
		#xbmc.Player().play(purl)
		item = xbmcgui.ListItem(path=purl)
		xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

def play_ltorrent(url, ind):
	ltorrent = LTorrentClient()
	ltorrent.url = 'http://127.0.0.1:8888'
	try:
		if url.startswith('http'): 	play_url = ltorrent.lt_play({'url': url}, ind)
		else:						play_url = ltorrent.lt_play({'file': url}, ind)
		item = xbmcgui.ListItem(path=play_url)
		xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
		xbmc.sleep(300)
		while not abortRequested() and ltorrent.isPlaying():
			xbmc.sleep(500)
	finally:
		ltorrent.lt_stop()


def get_item_name(url, ind):
	try:    name = List(url)[ind][0]
	except: name = ' '
	return name

def restream_ace(url):
	return 'http://127.0.0.1:8095/restream/'+url

def get_ace_status():
	stat_url=__settings__.getSetting("stat_url")
	j=eval(GET(stat_url).replace('null','"null"'))["response"]
	if j=={}:
		return '{}'
	else:
		status=j['status'] #if status=='dl': 
		try:
			progress=j['total_progress']
			if progress > 99: return 'Загрузка завершена'
			
			download=j['downloaded']
			seeds=j['peers']
			speed=j['speed_down']
			return "Загружено "+str(int(download/1024/1024))+" MB ("+str(progress)+" %) \nСиды: "+str(seeds)+" \nСкорость: "+str(speed)+' Kbit/s'
		except:
			return 'err'

def get_lt2http_status():
	if __settings__.getSetting("lt_api")=='0':  return lt2h.status_string()
	
	#i = lt2h.statusTorrent(LT2HASH)
	lt2h_host = __settings__.getSetting("lt_serv")
	lt2h_port = __settings__.getSetting("lt_port")
	host = 'http://'+lt2h_host+':'+str(lt2h_port)
	i = eval(GET(host+'/torrents/'+str(LT2HASH)+'/status'))
	try:
		seeds=i["seeders"]
		speed=int(i["download_rate"]/1024)
		progress=int(i["progress"]*100)
		download=int(i["total_download"]/1024/1024)
		return "Загружено: "+str(download)+" MB ("+str(progress)+" %) \nСиды: "+str(seeds)+" \nСкорость: "+str(speed)+' Kbit/s'
	except:
		return "err"


def get_ts_status():
	if __settings__.getSetting("ts_api")=='1': return get_ts2_status()
	try:
		false=False
		true=True
		null=None
		i=engine_ts.stat()
		seeds=i["ConnectedSeeders"]
		speed=int(i["DownloadSpeed"]/1024)
		download=int(i["LoadedSize"]/1024/1024)
		size = int(i['FileStats'][index_ts]['Length'])
		progress= int(float(download) * 100 / size)
		return "Загружено: "+str(download)+" MB ("+str(progress)+" %) \nСиды: "+str(seeds)+" \nСкорость: "+str(speed)+' Kbit/s'
	except:
		return 'err'

def get_ts2_status_old():
	deb_print('=ts2_status=')
	host = str(__settings__.getSetting("ts_serv"))
	port = str(__settings__.getSetting("ts_port"))
	CID  = __settings__.getSetting("ts_CID")
	FID  = int(__settings__.getSetting("ts_FID"))
	uri  = 'http://'+host+':'+port+'/torrent/stat'
	post = '{"Hash":"'+CID+'"}'
	json = POST(uri, post)
		
	try:
		false=False
		true=True
		null=None
		i=eval(json)
		seeds=i["ConnectedSeeders"]
		speed=int(i["DownloadSpeed"]/1024)
		download=int(i["LoadedSize"]/1024/1024)
		try:
			size = int(i['FileStats'][FID]['Length'])
			progress= int(float(download) * 100 / size)
		except:
			size = 0
			progress = 0
		return "Загружено: "+str(download)+" MB ("+str(progress)+" %) \nСиды: "+str(seeds)+" \nСкорость: "+str(speed)+' Kbit/s'
	except:
		return 'err'

def get_ts2_status():
	deb_print('=ts2_status=')
	VER  = __settings__.getSetting("ts_VER")
	if 'MatriX' not in VER: return get_ts2_status_old()
	host = str(__settings__.getSetting("ts_serv"))
	port = str(__settings__.getSetting("ts_port"))
	CID  = __settings__.getSetting("ts_CID")
	FID  = int(__settings__.getSetting("ts_FID"))
	uri  = 'http://'+host+':'+port+'/stream/fname?link='+CID+'&index='+str(FID)+'&stat'
	#post = '{"Hash":"'+CID+'"}'
	json = GET(uri)
		
	try:
		false=False
		true=True
		null=None
		j=eval(json)
		try: status = j["stat"]
		except: status = 0
		try: peers = j["total_peers"]
		except: peers = 0
		try: seeders = j["connected_seeders"]
		except: seeders = 0
		try: preload_size = j['preload_size']
		except: preload_size = 32*1024*1024
		try: download = j['preloaded_bytes']
		except: download = 0
		try: speed = j['download_speed']*8
		except: speed = 0
		try:
			size = int(j['file_stats'][FID]['length'])
			progress= int(float(download) * 100 / size)
		except:
			size = 0
			progress = 0
		return "Загружено: "+str(int(download/1024/1024))+" MB ("+str(progress)+" %) \nСиды: "+str(seeders)+" \nСкорость: "+str(int(speed/1024))+' Kbit/s'
	except:
		return 'err'

def get_t2h_status():
	try:
		from torrent2http import MediaType
		try:
			status   = engine_t2h.status()
			speed    = status.download_rate / 1024 * 8
			seeds    = status.num_seeds
		except:
			speed    = '?????'
			seeds    = '?'
		
		try:    tdownload = status.total_download / 1024 / 1024
		except: tdownload = '???'
		
		try:
			files = engine_t2h.list(media_types=[MediaType.VIDEO])
			file_id = files[0].index
			file_status = engine_t2h.file_status(file_id)
			download = file_status.download / 1024 / 1024
		except:
			download = tdownload
		#
		return "Загружено: "+str(int(download))+" MB \nСиды: "+str(seeds)+" \nСкорость: "+str(int(speed))+' Mbit/s'
	except:
		return 'err'

def Add2List(n):
	L2=[]
	try:L=eval(__settings__.getSetting("List"))
	except: L=[]
	if len(L)> 99: L=L[1:]
	
	for i in L:
		if i['title']!=n['title'] and i['url']!=n['url']: L2.append(i)
		elif i['url']==n['url']: n=i
	
	if str(n['title']).startswith('http'):
		if n['info']!={}: 
			try: 
				title = n['info']['title']
				if title!='': n['title'] = title
			except: pass
	
	if str(n['title']).startswith('http'):
			try: 
				title = name_bencode(n['url'])
				if title!='': n['title'] = title
			except: pass

	L2.append(n)
	__settings__.setSetting("List", repr(L2))

def RemList(url):
	L2=[]
	try:L=eval(__settings__.getSetting("List"))
	except: L=[]
	for i in L:
		if i['url']!=url: L2.append(i)
	__settings__.setSetting("List", repr(L2))
	if __settings__.getSetting("TorrDir") in url and __settings__.getSetting("del_on")=='true': xbmcvfs.delete(url)

def RenameList(url):
	L2=[]
	try:L=eval(__settings__.getSetting("List"))
	except: L=[]
	for i in L:
		if i['url']!=url: L2.append(i)
		else:
			t=i['title']
			t=inputbox(t)
			ni=i
			if t!='':
				ni['title']=t
				L2.append(ni)
			else: 
				L2.append(i)
	__settings__.setSetting("List", repr(L2))
	#if __settings__.getSetting("TorrDir") in url and __settings__.getSetting("del_on")=='true': xbmcvfs.delete(url)

def root():
	if __settings__.getSetting("open_on")== 'true': xbmcplugin.addDirectoryItem(handle, sys.argv[0]+'?mode=file', xbmcgui.ListItem('[B][ Открыть файл ][/B]'), True)
	if __settings__.getSetting("open_url")== 'true': xbmcplugin.addDirectoryItem(handle, sys.argv[0]+'?mode=link', xbmcgui.ListItem('[B][ Открыть ссылку ][/B]'), True)
	#if __settings__.getSetting("dir_on") == 'true': 
	try:GetDir()
	except: pass
	
	try:L=eval(__settings__.getSetting("List"))
	except: L=[]
	
	if L==[]:
		Ld=[
		['test torrent','http://td-soft.narod.ru/suits.torrent'],
		['test magnet','magnet:?xt=urn:btih:3bf8d2203474bde4189546c8f33e6a65cbabfe62&tr=http://bt.animedia.tv/announce.php&tr=retracker.local/announce'],
		['test CID','acestream://ef9778d589f3d3e90a479318e4078a81ca2bfc5f'],
		]
		for i in Ld:
					listitem = xbmcgui.ListItem(i[0])
					uri = sys.argv[0]+'?mode=open&url='+quote(i[1])
					xbmcplugin.addDirectoryItem(handle, uri, listitem, True)
	
	L.reverse()
	
	for i in L:
		try:
			try:info = i["info"]
			except: info = {}
			title= i["title"]
			url  = i["url"]
			try:    cover=info['cover']
			except: cover=icon
			try:    fanart=info['fanart']
			except: fanart=''
			Context=[('[B]Удалить[/B]', 'Container.Update("plugin://plugin.video.tam/?mode=rem&url='+quote(url)+'")'), ('[B]Переименовать[/B]', 'Container.Update("plugin://plugin.video.tam/?mode=rename&url='+quote(url)+'")'), ('[B]Очистить историю[/B]', 'Container.Update("plugin://plugin.video.tam/?mode=clear")')]
			listitem = xbmcgui.ListItem(title)#, iconImage=cover, thumbnailImage=cover)
			try:listitem.setInfo(type = "Video", infoLabels = info)
			except: pass
			try: listitem.setArt({ 'poster': cover, 'fanart' : fanart, 'thumb': cover, 'icon': cover})
			except: pass
			try: listitem.setProperty('fanart_image', fanart)
			except: pass
			uri = 'plugin://plugin.video.tam/?mode=open&url='+quote(url)+'&info='+quote(repr(info))#sys.argv[0]+
			listitem.addContextMenuItems(Context)
			xbmcplugin.addDirectoryItem(handle, uri, listitem, True)
		except:
			pass
	
	xbmcplugin.endOfDirectory(handle)

def GetDir():
	L1=[]
	try:L=eval(__settings__.getSetting("List"))
	except: L=[]
	if len(L)> 99: L=L[1:]
	
	path = __settings__.getSetting("TorrDir")
	if path == '' or path == None: return
	
	try: files = xbmcvfs.listdir(path)[1]
	except: files = []
	
	m_list=[]
	for i in files:
			if '.magnet' in i or '.MAGNET' in i:
				fn = os.path.join(path,i)
				fl = xbmcvfs.File(fn)
				url=fl.read()
				m_list.append(url)
				fl.close()
		
	lu=[]
	for i in L:
		lu.append(i['url'])
		if path in i['url']:
			if __settings__.getSetting("dir_on") == 'true':
				if xbmcvfs.exists(i['url']) or os.path.isfile(i['url']):
															L1.append(i)
		elif 'magnet:' in i['url']:
			if __settings__.getSetting("dir_on") == 'true': L1.append(i)
			elif i['url'] not in m_list: 					L1.append(i)
		else: 												L1.append(i)
	
	L=L1
	if __settings__.getSetting("dir_on") == 'true':
		for i in files:
			if '.torrent' in i or '.TORRENT' in i:
				url = os.path.join(path,i)
				if url not in lu:
					title = ''
					if __settings__.getSetting("b_name") == 'true':
						try: title = name_bencode(url)
						except: pass
					if title == '': title = i.replace('.torrent','').replace('.TORRENT','')
					n={'title':title, 'url':url}
					L.append(n)
		
		for i in files:
			if '.magnet' in i or '.MAGNET' in i:
				fn = os.path.join(path,i)
				fl = xbmcvfs.File(fn)
				url=fl.read()
				fl.close()
				if 'dn=' in url: title = mfind(url+'&','dn=', '&')
				else: title = i.replace('.magnet','').replace('.MAGNET','')
				n={'title':title, 'url':url}
				if url not in lu:
					L.append(n)

	__settings__.setSetting("List", repr(L))


def Open(url, info={}, purl='', engine=''):
	try:    cover=info['cover']
	except: cover=icon
	try:    fanart=info['fanart']
	except: fanart=''
	try:    ttl=info['title']
	except: 
		if 'magnet:' in url and 'dn=' in url: ttl = mfind(url+'&','dn=', '&')
		else: ttl=url
	try:    history=info['history']
	except: history=True

	if history: Add2List({'info':info, 'title':ttl, 'url':url.replace('http://127.0.0.1:8095/cache/','').replace('http://127.0.0.1:8095/proxy/','')})
	
	L=List(url)
	if len(L)==1 and history:
		if __settings__.getSetting("Autoplay")=='true':
			xbmc.executebuiltin('PlayMedia("plugin://plugin.video.tam/?mode=play&url='+quote(url)+'")')
			xbmcplugin.endOfDirectory(handle, False, False)
			return
	
	ind=0
	quote_info = quote(repr(info))
	quote_purl = quote(purl)
	for i in L:
		try:name=str(i[0])
		except:name=i[0]
		
		listitem = xbmcgui.ListItem(name)#, iconImage=cover, thumbnailImage=cover)
		try: 
			if len(i)>2: IL={'sorttitle': i[2]}
			else:        IL={'sorttitle': i[0]}
			listitem.setInfo(type = "Video", infoLabels = IL)#info
		except: pass
		try: listitem.setArt({ 'poster': cover, 'fanart' : fanart, 'thumb': cover, 'icon': cover})
		except: pass
		try:listitem.setProperty('fanart_image', fanart)
		except: pass
		listitem.setProperty('IsPlayable', 'true')
		Context=[]
		try:
			if info == {}: 
				info = {'originaltitle': name, 'year':ind}
				quote_info = quote(repr(info))
			Context.append(('[B]Настройки ТАМ[/B]', 'Container.Update("plugin://plugin.video.tam/?mode=settings")'))
			if len(L)>1: Context.append(('[B]Сохранить как сериал[/B]', 'Container.Update("plugin://plugin.video.tam/?mode=save_series&url='+quote(url)+'&info='+quote_info+'&purl='+quote_purl+'")'))
			if len(L)<5: Context.append(('[B]Сохранить как фильм[/B]', 'Container.Update("plugin://plugin.video.tam/?mode=save_movie&url='+quote(url)+'&info='+quote_info+'&ind='+str(ind)+'&purl='+quote_purl+'")'))
			Context.append(('[B]Сохранить torrent[/B]', 'Container.Update("plugin://plugin.video.tam/?mode=save_torrent&url='+quote(url)+'&info='+quote_info+'&ind='+str(ind)+'&purl='+quote_purl+'")'))
			listitem.addContextMenuItems(Context)
		except: pass
		
		uri = sys.argv[0]+'?mode=play&ind='+str(ind)+'&url='+quote(url)+'&engine='+quote(engine)
		
		if media(name): xbmcplugin.addDirectoryItem(handle, uri, listitem)
		ind+=1
	
	#xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
	xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
	xbmcplugin.endOfDirectory(handle)
	#xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
	xbmc.sleep(300)
	if history: SetViewMode()

def List(url):
	deb_print('== TAM List ==')
	deb_print(url)
	if __settings__.getSetting('tor2mag')=='1' and 'magnet:' in url:
		cache=magnet_cache(url)
		if cache!=[]: return cache
		url=m2t(url)
	if 'magnet:' in url: 				return list_magnet(url)
	elif 'acestream:' in url: 			return list_ace(url)
	else: 								return list_bencode(url)

def list_magnet(url):
	cache=magnet_cache(url)
	if cache!=[]: return cache
	if __settings__.getSetting('Engine2') == '0':
		if __settings__.getSetting('Engine') == '0' or __settings__.getSetting('Engine') == '5':
				try: 		return list_ace(url)
				except:
					try:    return list_ts(url)
					except: return list_lt2http(url)
		elif __settings__.getSetting('Engine') == '1':
				try: 		return list_t2h(url)
				except:
					try:    return list_ts(url)
					except: return list_ace(url)
		elif __settings__.getSetting('Engine') == '2':
				try: 		return list_yatp(url)
				except:
					try:    return list_ts(url)
					except: return list_ace(url)
		elif __settings__.getSetting('Engine') == '6':
				try: 
					L=list_lt2http(url)
					if L!=[]: return L
					else: return [['Ошибка загрузки контента[COLOR 01000000].ts[/COLOR]', 0]]
				except: return [['Ошибка загрузки контента[COLOR 01000000].ts[/COLOR]', 0]]
		else:
				try: 		return list_ts(url)
				except:
					try:    return list_ace(url)
					except: return list_t2h(url)
	if __settings__.getSetting('Engine2') == '1': 
							return [['Начать просмотр[COLOR 01000000].ts[/COLOR]', 0]]
	if __settings__.getSetting('Engine2') == '2': 
							try: return list_ace(url)
							except: return [['Ошибка загрузки контента[COLOR 01000000].ts[/COLOR]', 0]]
	if __settings__.getSetting('Engine2') == '3': 
							try: return list_ts(url)
							except: return [['Ошибка загрузки контента[COLOR 01000000].ts[/COLOR]', 0]]
	if __settings__.getSetting('Engine2') == '4': 
							list_p2h(url)
							try: return list_t2h(url)
							except: return [['Ошибка загрузки контента[COLOR 01000000].ts[/COLOR]', 0]]
	if __settings__.getSetting('Engine2') == '5': 
							try: return list_yatp(url)
							except: return [['Ошибка загрузки контента[COLOR 01000000].ts[/COLOR]', 0]]
	if __settings__.getSetting('Engine2') == '6': 
							try: 
								L=list_lt2http(url)
								if L!=[]: return L
								else: return [['Ошибка загрузки контента[COLOR 01000000].ts[/COLOR]', 0]]
							except: return [['Ошибка загрузки контента[COLOR 01000000].ts[/COLOR]', 0]]

def list_bencode(url):
	deb_print('== TAM list_bencode ==')
	deb_print(url)
	if url.startswith('http'): 
		cache=torrent_cache(url)
		if cache!=[]: return cache
		
		torrent_data = GET(url, cache = True)
		if err_torrent(torrent_data) and '127.0.0.1' not in url: 
			torrent_data = GET(unlock_url(url, True))
		
	elif url.startswith('file:'): 
		torrent_data = GET(url, cache = True)
	else: 
		torrent_data = READ(url)
	
	L2=[]
	L3=[]
	if err_torrent(torrent_data)==False: #if torrent_data != None and torrent_data != '':
		import bencode
		torrent = bencode.bdecode(torrent_data)
		try:
			L = torrent['info']['files']
			ind=0
			for i in L:
				fp=''
				for p in i['path']:
					try: fp+=rt(p)+"-"
					except: fp=i['path'][-1]
				L2.append([rt(i['path'][-1]), ind, fp])
				#try: L2.append([i['path'][-1].decode(), ind, fp])
				#except: 
				#	try:L2.append([i['path'][-1].decode('windows-1251'), ind, fp]) 
				#	except: L2.append([i['path'][-1], ind, fp])
				L3.append(L2[-1][0])
				ind+=1
		except:
			try:
				try: ttl = rt(torrent['info']['name'])+'[COLOR 01000000].ts[/COLOR]'
				except: ttl = torrent['info']['name']+'[COLOR 01000000].ts[/COLOR]'
				L2.append([ttl, 0])
			except:
				L2.append(['Воспроизвести[COLOR 01000000].ts[/COLOR]', 0])
	if len(L3)>1: 
		save_cache(url, L3)
		if 'itorrents.org' in url: save_cache(t2m(url), L3)
	return L2

def list_ts(url):
	InstallAddon('script.module.torrserver')
	import torrserve_stream
	tss = torrserve_stream.Settings()
	ts =  torrserve_stream.Engine(uri=url, host=tss.host, port=tss.port)
	host = 'http://'+tss.host+':'+str(tss.port)
	hash=mfind(url+'&', 'btih:', '&')
	hash=ts.hash
	
	false=False
	true=True
	null=None
	xbmc.sleep(1000)
	stat=ts.stat()
	L2s=stat['FileStats']
	L2=stat.get('RealIdFileStats', L2s)
	if not L2: L2=L2s
	#L2=ts.stat()['FileStats']
	#print L2
	L3=[]
	Lc=[]
	for ind in range(0, len(L2)+1):
		for i in L2:
			if i['Id'] == ind:
				L3.append([i['Path'],ind])
				Lc.append(i['Path'])
				if sys.version_info.major > 2: deb_print(str(i['Id'])+' '+i['Path'])
	if Lc!=[]: save_cache(url, Lc)
	return L3

def list_lt2http(url):
	lt2h_host = __settings__.getSetting("lt_serv")
	lt2h_port = __settings__.getSetting("lt_port")
	host = 'http://'+lt2h_host+':'+str(lt2h_port)
	hash=mfind(url+'&', 'btih:', '&')
	
	false=False
	true=True
	null=None
	r = GET(host+'/service/add/uri?uri='+quote(url)+'&storage=file', True)
	
	#t_add = False
	for i in range (15):
		xbmc.sleep(1000)
		L=eval(GET(host+'/torrents', True))
		for t in L:
			if hash == t['hash']: break
	
	L2=eval(GET(host+'/torrents/'+hash+'/files', True))
	L3=[]
	Lc=[]
	for ind in range(0, len(L2)):
		for i in L2:
			if i['id'] == ind:
				L3.append([i['name'],ind])
				Lc.append(i['name'])
				deb_print(str(i['id'])+' '+i['name'])
	if Lc!=[]: save_cache(url, Lc)
	clear_lt2http()
	return L3

def list_yatp(url):
	url=url.lower()
	false=False
	true=True
	null=None
	
	host = 'http://127.0.0.1:8668/json-rpc'
	hash=mfind(url+'&', 'btih:', '&')
	
	post='{"method": "get_files", "params": {"info_hash":"'+hash+'"}}'
	json = eval(POST(host, post))
	
	if 'error' in json.keys():
	
		post='{"method": "add_torrent", "params": {"torrent":"'+url+'", "paused":true}}'
		json = eval(POST(host, post))
		
		post='{"method": "check_torrent_added"}'
		for p in range(20):
			xbmc.sleep(1000)
			json = eval(POST(host, post))
			if json['result']==True: break
		
		post='{"method": "get_files", "params": {"info_hash":"'+hash+'"}}'
		json = eval(POST(host, post))
		
		post='{"method": "remove_torrent", "params": {"info_hash":"'+hash+'", "delete_files": false}}'
		POST(host, post)
		
	L2=json['result']
	
	L3=[]
	Lc=[]
	ind=0
	for i in L2:
		t=i[0]
		if '\\' in t: t=t[t.rfind('\\')+1:]
		L3.append([t,ind])
		Lc.append(t)
		ind+=1
	if Lc!=[]: save_cache(url, Lc)
	return L3

def list_t2h(uri, tout=99):
		tout=tout*5
		#cache=magnet_cache(uri)
		#if cache!=[]: return cache
		InstallAddon('script.module.torrent2http')
		from contextlib import closing
		sys.path.append(os.path.join(xt("special://home/"),"addons","script.module.torrent2http","lib"))
		# Create instance of Engine 
		from torrent2http import State, Engine, MediaType
		
		engine = Engine(uri, enable_dht=True, dht_routers=["router.bittorrent.com:6881","router.utorrent.com:6881","acg.rip:6699","open.acgnxtracker.com:80","open.acgtracker.com:1096","opentracker.i2p.rocks:6969","pow7.com:80","tracker.gbitt.info:80","tracker.internetwarriors.net:1337","tracker.kamigami.org:2710","tracker.lelux.fi:80","tracker.nyap2p.com:8080","tracker.torrentyorg.pl:80","tracker.yoshi210.com:6969","tracker01.loveapp.com:6789","tracker1.itzmx.com:8080","tracker2.itzmx.com:6961","tracker3.itzmx.com:6961","tracker4.itzmx.com:2710","vps02.net.orel.ru:80","www.loushao.net:8080","www.proxmox.com:6969","tracker.gbitt.info:443","tracker.lelux.fi:443","tracker.parrotlinux.org:443","h4.trakx.nibba.trade:80","mail2.zelenaya.net:80","retracker.sevstar.net:2710","t.nyaatracker.com:80","tracker.bt4g.com:2095","tracker.bz:80","tracker.corpscorp.online:80","tracker.opentrackr.org:1337","tracker.tvunderground.org.ru:3218"], user_agent = 'uTorrent/2200(24683)')#AL[]
		files = []
		# Ensure we'll close engine on exception 
		progressBar = xbmcgui.DialogProgress()
		progressBar.create('Torrent2Http', 'Запуск')
		with closing(engine):
		# Start engine 
			engine.start()
			# Wait until files received 
			while not files and not abortRequested():
				try:progressBar.update(0, 'Torrent2Http', 'Примагничиваемся', "")
				except:progressBar.update(0, 'Примагничиваемся')
				# Will list only video files in torrent
				files = engine.list(media_types=[MediaType.VIDEO])
				# Check if there is loading torrent error and raise exception 
				engine.check_torrent_error()
				xbmc.sleep(200)
				tout-=1
				if progressBar.iscanceled() or abortRequested() or tout<0:
							progressBar.update(0)
							progressBar.close()
							return []
				
		progressBar.close()
		
		if files==None: return []
		L=[]
		for i in files:
			L.append(i[0])
		save_cache(uri, L)
		return files


def list_ace(url):
	deb_print('==list_ace==')
	try:
		engine=get_engine()
		if engine=="0" or engine=="6": ACE_start()
	except: pass
	
	progressBar = xbmcgui.DialogProgress()
	#progressBar.create('ACE', 'Примагничиваемся')
	srv=__settings__.getSetting("p2p_serv")
	prt=__settings__.getSetting("p2p_port")
	
	if 'btih:' in url:
		if '&' not in url: url=url+'&'
		CID=mfind(url+'&', 'btih:', '&')
		as_url='http://'+srv+':'+prt+'/ace/getstream?infohash='+CID+"&format=json"
	elif 'acestream:' in url:
		CID=url.replace('acestream://','')
		as_url='http://'+srv+':'+prt+'/ace/getstream?id='+CID+"&format=json"
	else:
		as_url='http://'+srv+':'+prt+'/ace/getstream?url='+url+"&format=json"
	
	m3u=GET(as_url)
	
	if '#EXTINF' not in m3u: 
						if 'failed to load content' in m3u: return [['Ошибка загрузки контента[COLOR 01000000].ts[/COLOR]', 0]]
						else: 
							if '&dn=' in url: 
								ttl = unquote(mfind(url+'&','dn=', '&'))
								return [[ttl+'[COLOR 01000000].ts[/COLOR]', 0]]
							else: 
								return [['Начать просмотр[COLOR 01000000].ts[/COLOR]', 0]]
	
	L = m3u.splitlines()
	Lt=[]
	Lu=[]
	for e in L:
		if '#EXTINF' in e: Lt.append(e.replace('#EXTINF:-1,',''))
		if 'http:'   in e: Lu.append(e)
	
	LL=[]
	Lc=[]
	for n in range(0, len(Lu)):
		for i in range(0, len(Lu)):
			u=Lu[i]
			ind=int(u[u.rfind('idx=')+4:])
			if ind == n: 
				LL.append ([Lt[i], Lu[i]])
				Lc.append (Lt[i])
			
	#progressBar.close()
	if Lc!=[]: save_cache(url, Lc)
	return LL

def clear_lt2http():
	lt2h_host = __settings__.getSetting("lt_serv")
	lt2h_port = __settings__.getSetting("lt_port")
	lt2h_list = int(__settings__.getSetting("lt_list"))
	host = 'http://'+lt2h_host+':'+str(lt2h_port)
	
	false=False
	true=True
	null=None
	L=eval(GET(host+'/torrents', True))
	if len(L) > lt2h_list:
		for ind in range(0, len(L)-lt2h_list):
			i=L[ind]
			hash=i['hash']
			GET(host+'/torrents/'+hash+'/remove', True)

def name_bencode(url):
	deb_print('== TAM name_bencode ==')
	deb_print(url)
	if url.startswith('http'): 
		torrent_data = GET(url, cache = True)
		if torrent_data == None: torrent_data = ''
		if err_torrent(torrent_data) and '127.0.0.1' not in url: torrent_data = GET(unlock_url(url, True))
	elif 'file:' in url: torrent_data = GET(url, cache = True)
	else: torrent_data = None
	
	if torrent_data == None: torrent_data = READ(url)
	if torrent_data != None:
		import bencode
		torrent = bencode.bdecode(torrent_data)
		try: ttl = rt(torrent['info']['name'])
		except: ttl = torrent['info']['name']
	return ttl


try:
	import magnetdb
	magnetdb.temp_dir=addon.getAddonInfo('path')
except:
	pass


def get_hash(url):
	hash = ''
	if 'magnet:' in url: 
		url += '&'
		hash=url[url.find('btih:')+5:url.find('&')].lower()
	elif 'acestream:' in url: hash = '' # не хешируем, может потом сделаю
	else: 
		url=t2m(url)
		if 'btih:' in url: hash=url[url.find('btih:')+5:url.find('&')].lower()
		else: hash = ''
	
#def get_list_cache(url):
#	hash = get_hash(url)

def get_web_cache(uri):
	if __settings__.getSetting('GCache')=='false': return []
	if 'btih:' in uri :
		try:
			hash=uri[uri.find('btih:')+5:uri.find('&')].lower()
			L=magnetdb.get_info(hash)['list']
			return L
		except:
			return []

#print(magnetdb.get_info('51b097c442949600e328ae0a92a9a724e19465db')['list'])

def add_web_cache(uri, L):
	if __settings__.getSetting('GCache')=='false': return []
	if 'btih:' in uri:
		try:
			hash=uri[uri.find('btih:')+5:uri.find('&')].lower()
			path=xt(os.path.join(addon.getAddonInfo('path'), 'cache', hash))
			if os.path.exists(path)== True: return []
			info = {'id': hash, 'list': L}
			magnetdb.add(info)
		except:
			pass

def magnet_cache(uri):
	deb_print('-- magnet_cache --')
	if 'magnet:' not in uri: return
	hash=uri[uri.find('btih:')+5:uri.find('&')]
	path=xt(os.path.join(addon.getAddonInfo('path'), 'cache', hash))
	
	if os.path.exists(path)== True:
		try:
			fl = open(path, "r")
			cache = eval(fl.read())
			fl.close()
			L=[]
			ind=0
			for i in cache:
				L.append([i,ind])
				ind+=1
			#if L!=[]: add_web_cache(uri, cache)
			return L
		except: 
			return []
	else:
		cache=get_web_cache(uri)
		if cache!=[]: save_cache(uri, cache, False)
		else: return []
		ind=0
		L=[]
		for i in cache:
			L.append([i,ind])
			ind+=1
		return L

def torrent_cache(uri):
	deb_print('-- torrent_cache --')
	crc = CRC32(uri)
	path=xt(os.path.join(addon.getAddonInfo('path'), 'cache', crc))
	if os.path.exists(path)== True:
		try:
			fl = open(path, "r")
			Dc = eval(fl.read())
			fl.close()
			cache = Dc['data']
			tm = Dc['tm']
			if time.time() - tm > 3600*4: return []
			L=[]
			ind=0
			for i in cache:
				L.append([i,ind])
				ind+=1
			return L
		except: 
			return []
	else:
		return []

def save_cache(uri, cache, webc=True):
	deb_print('save_cache')
	try:
		if 'magnet:' in uri:
			hash=uri[uri.find('btih:')+5:uri.find('&')]
			deb_print(hash)
			if webc: add_web_cache(uri, cache)
			path=xt(os.path.join(addon.getAddonInfo('path'), 'cache', hash))
			fl = open(path, "w")
			fl.write(repr(cache))
			fl.close()
		elif url.startswith('http'):
			crc = CRC32(uri)
			path=xt(os.path.join(addon.getAddonInfo('path'), 'cache', crc))
			fl = open(path, "w")
			fl.write(repr({'tm':time.time(),'data':cache}))
			fl.close()
	except:
		showMessage ('error', 'save_cache')

def select_cover(title):
	deb_print('== select_icon ==')
	url='https://yandex.ru/images/search?text='+quote(title)+'%20cover&isize=small&iorient=vertical&itype=jpg&lr=193'
	hp=GET(url)
	ss='&quot;img_href&quot;:&quot;'
	L=mfindal(hp, ss, '&quot;')
	for i in L:
		if 'http' in i:
			cover=i.replace(ss,'')
			listitem = xbmcgui.ListItem(title, iconImage=cover, thumbnailImage=cover)
			uri = sys.argv[0]+'?mode=set_cover&url='+quote(cover)
			xbmcplugin.addDirectoryItem(handle, uri, listitem, True)
	
	xbmcplugin.endOfDirectory(handle)

def set_cover(url):
			saver_data = eval(__settings__.getSetting("saver_data"))
			info = saver_data['info']
			info['cover']=url
			saver_data['info'] = info
			__settings__.setSetting("saver_data", repr(saver_data))


def ACE_start():
	srv=__settings__.getSetting("p2p_serv")
	prt=__settings__.getSetting("p2p_port")
	lnk='http://'+srv+':'+prt+'/webui/api/service?method=get_version&format=jsonp&callback=mycallback'#getstream?id='+CID
	pDialog = xbmcgui.DialogProgressBG()
	resp=GET(lnk)
	if resp != '' and resp != None:
		return False
	else:
		#showMessage('ТАМ', 'Запуск Ace Stream')
		pDialog.create('ТАМ', 'Запуск Ace Stream ...')
		pDialog.update(0, message='Запуск Ace Stream ...')
		start_linux()
		start_windows()
		for i in range (0,10):
			if abortRequested(): break
			pDialog.update(i*10, message='Запуск Ace Stream ...')
			xbmc.sleep(1500)
			if abortRequested(): break
			resp=GET(lnk)
			if resp != '' and resp != None:
				pDialog.close()
				return True
		
		pDialog.close()
		return False

def start_linux():
        import subprocess
        try:
            subprocess.Popen(['acestreamengine', '--client-console'])
        except:
            try:
                subprocess.Popen('acestreamengine-client-console')
            except: 
                try:
                    xbmc.executebuiltin('XBMC.StartAndroidActivity("org.acestream.media")')
                    xbmc.sleep(2000)
                    xbmc.executebuiltin('XBMC.StartAndroidActivity("org.xbmc.kodi")')
                except:
                    return False
        return True

def start_windows():
        try:
            try: import _winreg
            except: import winreg as _winreg
            try:
                t = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, r'Software\AceStream')
            except:
                t = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, r'Software\TorrentStream')
            path = _winreg.QueryValueEx(t, r'EnginePath')[0]
            os.startfile(path)
            return True
        except:
            return False

def SetViewMode():
	n = int(__settings__.getSetting("ListView"))
	if n>0:
		xbmc.executebuiltin("Container.SetViewMode(0)")
		for i in range(1,n):
			xbmc.executebuiltin("Container.NextViewMode")


def open_torrent_list(L, info):
	__settings__.setSetting("saver_data", repr({'list':L, 'info':info}))
	import saver
	saver.open_list()


def get_params():
	param=[]
	paramstring=sys.argv[2]
	if len(paramstring)>=2:
		params=sys.argv[2]
		cleanedparams=params.replace('?','')
		if (params[len(params)-1]=='/'):
			params=params[0:len(params)-2]
		pairsofparams=cleanedparams.split('&')
		param={}
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]
	return param

params = get_params()
#print (params)

try:mode = unquote(params["mode"])
except:mode =""
try:name = unquote(params["name"])
except:name =""
try:url = unquote(params["url"])
except:url =""
try:purl = unquote(params["purl"])
except:purl =""
try:ind = unquote(params["ind"])
except:ind ="0"
try:engine = unquote(params["engine"])
except:engine = ""
try:L = eval(unquote(params["L"]))
except:L =[]
try:ss = eval(unquote(params["s"]))
except:ss = []
try:ee = eval(unquote(params["e"]))
except:ee = []
try:nf = int(unquote(params["nf"]))
except:nf = 0
#print (params["info"])
#info = eval(unquote(params["info"]))
try:info = eval(unquote(params["info"]))
except:info = {}
try:manual = eval(unquote(params["manual"]))
except:manual = True
try:ad = eval(unquote(params["ad"]))
except:ad = 0


print (url)

proxy_list=[
	'http://www.pitchoo.net/zob_/index.php?q=',  #Франция
	'http://thely.fr/proxy/?q=',                 #Франция
	'http://xawos.ovh/index.php?q=',             #Франция
	'http://prx.afkcz.eu/prx/index.php?q=',      #Чехия
	'https://derzeko.de/Proxy/index.php?q=',     #Германия
	'https://dev.chamoun.fr/proxy/index.php?q=', #Франция
	'http://www.proxy.zee18.info/index.php?q=',  #Великобритания
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


def editor(url):
	return 'http://127.0.0.1:8095/unlocker/'+url

def unlock_url(url, forced = False):
	if 'magnet:' in url: return url
	if err_torrent(GET(url, cache = True)) == False: return url
	for proxy in proxy_list:
		url=url.replace(proxy, 'http://127.0.0.1:8095/torrent/')
	if forced and '127.0.0.1' not in url: 
		url='http://127.0.0.1:8095/proxy/'+url
	return url

def cache_torrent(url):
	orig_url = url
	if 'magnet:' in url: return url
	for proxy in proxy_list:
		url=url.replace(proxy, 'http://127.0.0.1:8095/torrent/')
	if  '8095/proxy/' in url:  url=url.replace('8095/proxy/', '8095/cache/')
	if '127.0.0.1' not in url: url='http://127.0.0.1:8095/cache/'+url
	
	try:
		r=GET(url)
		if 'd8:' in r or 'd7:' in r or ':announc' in r: return url
		else: return orig_url
	except: pass
	return url

if __settings__.getSetting('tor2mag')=='2' and 'magnet:' in url: url=m2t(url)

#if __settings__.getSetting('tcache')=='true' and 'http' in url: url=cache_torrent(url)
if __settings__.getSetting('unlock')!='0' and '127.0.0.1' not in url and url.startswith('http'): url=unlock_url(url, True)



if mode==""           : root()#select_cover('terminator')
if mode=="open"       : Open(url, info, purl, engine)
if mode=="history"    : Add2List({'info':info, 'title':info['title'], 'url':url})
if mode=="play"       : play(url, int(ind), ad)
if mode=="open_strm"  : open_strm(url, int(ind), purl, name)
if mode=="save_movie" : save_strm(url, int(ind), purl, info)
if mode=="save_series": save_series(url, info, purl)
if mode=="save_torrent":save_torrent(url, info)
if mode=="save"       : save(url, int(ind), purl, info)
if mode=="settings"   : __settings__.openSettings()
if mode=="rem"        : RemList(url)
if mode=="rename"     : RenameList(url)
if mode=="clear"      : __settings__.setSetting('List','[]')
if mode=="run"        : 
						xbmc.executebuiltin('Dialog.Close(all,true)')
						xbmc.executebuiltin('ActivateWindow(10025,"'+purl+'", return)')
						xbmc.sleep(1000)
						xbmc.executebuiltin('Container.Refresh()')
if mode=="file"       : 
	f=open_file()
	if f!={}: 
		if __settings__.getSetting("OpenMagnet")=='true'  or f['file']=='':
			Open(f['magnet'], {'title':f['title']})
		else:
			engine=get_engine()
			file=f['file']
			Open(file, {'title':f['title']})
if mode=="link"       : 
	url=inputbox()
	if url!='': Open(url)
if mode=='skip_ad'    : skip_ad()
if mode=='select_cover'     : select_cover(name)
if mode=='set_cover'        : set_cover(url)
if mode=='open_torrent_list': open_torrent_list(L, info)
#open_strm(url, ind, purl, info)

