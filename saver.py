# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, os, sys, time, urllib

PLUGIN_NAME   = 'plugin.video.tam'
#handle = int(sys.argv[1])
addon = xbmcaddon.Addon(id=PLUGIN_NAME)
__settings__ = xbmcaddon.Addon(id=PLUGIN_NAME)
icon = xbmc.translatePath(os.path.join(addon.getAddonInfo('path'), 'icon.png'))
background = xbmc.translatePath(os.path.join(addon.getAddonInfo('path'), 'fanart.png'))

Ls=["Default", "Estuary"]
skin = Ls[int(__settings__.getSetting('skin'))]

def b2s(s):
	if sys.version_info.major > 2:
		try:s=s.decode('utf-8')
		except: pass
		try:s=s.decode('windows-1251')
		except: pass
		return s
	else:
		return s

if sys.version_info.major > 2:  # Python 3 or later
	from urllib.parse import urlencode, quote_plus
	from urllib.parse import urlparse
	from urllib.parse import quote
	from urllib.parse import unquote
	import urllib.request as urllib2
else:  # Python 2
	import urllib, urlparse
	from urllib import quote
	from urllib import unquote
	import urllib2



def log(text, x3=''):
	print(text)

#Action Codes
# See guilib/Key.h
ACTION_CANCEL_DIALOG = (9,10,51,92,110)
ACTION_PLAYFULLSCREEN = (12,79,227)
ACTION_MOVEMENT_LEFT = (1,)
ACTION_MOVEMENT_RIGHT = (2,)
ACTION_MOVEMENT_UP = (3,)
ACTION_MOVEMENT_DOWN = (4,)
ACTION_MOVEMENT = (1, 2, 3, 4, 5, 6, 159, 160)
ACTION_INFO = (11,)
ACTION_CONTEXT = (117,)
ACTION_MOVEMENT_ALL = (1, 2, 3, 4, 5, 6, 159, 160, 104, 105, 106, 107)


#ControlIds
CONTROL_CONSOLES = 500
CONTROL_GENRE = 600
CONTROL_YEAR = 700
CONTROL_PUBLISHER = 800
CONTROL_CHARACTER = 900
FILTER_CONTROLS = (500, 600, 700, 800, 900,)
GAME_LISTS = (50, 51, 52,53, 54, 55, 56, 57, 58)
CONTROL_SCROLLBARS = (2200, 2201, 60, 61, 62)

CONTROL_GAMES_GROUP_START = 600
CONTROL_GAMES_GROUP_END = 59

#CONTROL_BUTTON_CHANGE_VIEW = 2
CONTROL_BUTTON_FAVORITE = 1000
CONTROL_BUTTON_SEARCH = 1100
CONTROL_BUTTON_VIDEOFULLSCREEN = (2900, 2901,)
NON_EXIT_RCB_CONTROLS = (500, 600, 700, 800, 900, 2, 1000, 1100)

CONTROL_LABEL_MSG = 4000
CONTROL_BUTTON_MISSINGINFODIALOG = 4001

genres=['animation', 'action', 'comedy', 'drama', 'fantasy', 'historical', 'horror', 'thriller', 'western']


def ru(x):return unicode(x,'utf8', 'ignore')
def xt(x):return xbmc.translatePath(x)
def rt(s):
	if sys.version_info.major > 2: return s
	try:s=s.decode('utf-8')
	except: pass
	try:s=s.decode('windows-1251')
	except: pass
	s=s.encode('utf-8')
	return s

def fs_enc(path):
	path=xbmc.translatePath(path)
	sys_enc = sys.getfilesystemencoding() if sys.getfilesystemencoding() else 'utf-8'
	try:path2=path.decode('utf-8')
	except: pass
	try:path2=path2.encode(sys_enc)
	except: 
		try: path2=path2.encode(sys_enc)
		except: path2=path
	return path2

def fs_dec(path):
    sys_enc = sys.getfilesystemencoding() if sys.getfilesystemencoding() else 'utf-8'
    return path.decode(sys_enc).encode('utf-8')

def construct_request(params):
	try: pr = urllib.urlencode(params)
	except: pr = urlencode(params, quote_via=quote_plus)
	return '%s?%s' % ('plugin://plugin.video.tam/', pr)

def inputbox(t):
	skbd = xbmc.Keyboard(t)
	#skbd.setHeading('Поиск:')
	skbd.doModal()
	if skbd.isConfirmed():
		return skbd.getText()
	else:
		return ""

def GET(url,Referer = 'http://emulations.ru/'):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Opera/10.60 (X11; openSUSE 11.3/Linux i686; U; ru) Presto/2.6.30 Version/10.60')
	req.add_header('Accept', 'text/html, application/xml, application/xhtml+xml, */*')
	req.add_header('Accept-Language', 'ru,en;q=0.9')
	req.add_header('Referer', Referer)
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	return link

def get_picons(title):
	print('== select_icon ==')
	if " TV" not in title: title=title+" TV"
	url='http://yandex.ru/images/search?text='+quote(title)+'&isize=small&iorient=square'
	print(url)
	hp=GET(url)
	ss='&quot;img_href&quot;:&quot;'
	L=mfindal(hp, ss, '&quot;')
	L2=[]
	for i in L:
		if 'http' in i: L2.append(i.replace(ss,''))
	return L2

def mfindal(http, ss, es):
	L=[]
	while http.find(es)>0:
		s=http.find(ss)
		e=http.find(es, s+len(ss))
		i=http[s:e]
		L.append(i)
		http=http[e+2:]
	return L

def media(t):
	L = ['.avi', '.mov', '.mp4', '.mpg', '.mpeg', '.m4v', '.mkv', '.ts', '.vob', '.wmv', '.m2ts']
	for i in L:
		if i in t.lower(): return True
	return False

def find_s(t):
		S=['s','S']
		n=["0","1","2","3","4","5","6","7","8","9"]
		for i in S:
			for j in n:
				for k in n:
					ss=i+j+k
					if t.find(ss)>0: return t.find(ss)+1
		return -1

def find_e(t):
		S=['e','E','[']
		n=["0","1","2","3","4","5","6","7","8","9"]
		for i in S:
			for j in n:
				for k in n:
					ss=i+j+k
					if t.find(ss)>0: return t.find(ss)+1
		return -1


def save():
		nfo=__settings__.getSetting("save_nfo")
		saver_data = eval(__settings__.getSetting("saver_data"))
		
		name =__settings__.getSetting("save_title")
		info = saver_data['info']
		url  = saver_data['url']
		L    = saver_data['list']
		try:    ad = info['AD']
		except: ad = 0
		
		range_s=eval(__settings__.getSetting("range_s"))
		range_e=eval(__settings__.getSetting("range_e"))
		
		ind=0
		n=0
		so=''
		for i in L:
			n+=1
			if range_s[0] == 't': s=range_s[1]
			else: s=i[range_s[0]:range_s[1]]
			
			if so!=s: n=1
			if range_e[0] == 'i': 
				if n<10: e='0'+str(n)
				else:	 e=str(n)
			else:
				e=i[range_e[0]:range_e[1]]
			
			if media(i):
				epd = rt(name)+".s"+rt(s)+".e"+rt(e)
				save_strm(name, epd, url, ind, ad)
				if nfo == 'ДА': save_nfo(name, epd ,s , e, info)
			ind+=1
			so=s
		
		if nfo == 'ДА': save_tvshow_nfo(name, info)
		
		try:purl  = eval(__settings__.getSetting("saver_data"))['purl']
		except: purl  = ''
		if  __settings__.getSetting("SavePURL") == 'true' and purl!='': save_purl(name, purl, info)
		
		xbmc.executebuiltin('UpdateLibrary("video", "", "false")')


def save_strm(name, epd, url, ind, ad=0):
		name=name.replace("/"," ").replace("\\"," ").replace("?","").replace(":","").replace('"',"").replace('*',"").replace('|',"").replace('>',"").replace('<',"").strip()
		epd=epd.replace("/"," ").replace("\\"," ").replace("?","").replace(":","").replace('"',"").replace('*',"").replace('|',"").replace('>',"").replace('<',"").strip()
		try:
			if isinstance(name, unicode): name=name.encode('utf-8')
			if isinstance(epd, unicode): epd=epd.encode('utf-8')
		except:
			pass
		
		try:Directory= __settings__.getSetting("SaveDirectory2")
		except: Directory=os.path.join(addon.getAddonInfo('path'), 'strm')
		if Directory=="":Directory=os.path.join(addon.getAddonInfo('path'), 'strm')
		
		SaveDirectory = os.path.join(Directory, name)
		
		if os.path.isdir(fs_enc(SaveDirectory))==0: os.mkdir(fs_enc(SaveDirectory))
		
		uri = construct_request({
			'url'  : url,
			'title': epd,
			'ind'  : ind,
			'mode' : 'play',
			'ad'   : ad
		})
		fl = open(fs_enc(os.path.join(SaveDirectory, epd+'.strm')), "w")
		fl.write(uri)
		fl.close()

def save_tvshow_nfo(name, info={}):
		name=name.replace("/"," ").replace("\\"," ").replace("?","").replace(":","").replace('"',"").replace('*',"").replace('|',"").replace('>',"").replace('<',"").strip()
		try:title=name.encode('utf-8')
		except:title=name
		
		try:Directory= __settings__.getSetting("SaveDirectory2")
		except: Directory=os.path.join(addon.getAddonInfo('path'), 'strm')
		if Directory=="":Directory=os.path.join(addon.getAddonInfo('path'), 'strm')
		
		if isinstance(Directory, unicode): Directory=Directory.encode('utf-8')
			
		SaveDirectory = os.path.join(Directory, name)
		if os.path.isdir(fs_enc(SaveDirectory))==0: os.mkdir(fs_enc(SaveDirectory))
		
		try:year=info['year']
		except:year=0
		try:plot=info['plot']
		except:plot=''
		try:cover=info['cover']
		except:cover=''
		try:fanart=info['fanart']
		except:fanart=''
		try:genre=info['genre']
		except:genre=''
		try:title=info['title']
		except:pass

		nfo='<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'+chr(10)
		nfo='<tvshow>'+chr(10)
		
		nfo+="	<title>"+title+"</title>"+chr(10)
		nfo+="	<showtitle>"+title+"</showtitle>"+chr(10)
		nfo+="	<year>"+str(year)+"</year>"+chr(10)
		nfo+="	<season>-1</season>"+chr(10)
		nfo+="	<genre>"+genre+"</genre>"+chr(10)
		nfo+="	<plot>"+plot+"</plot>"+chr(10)
		nfo+="	<fanart><thumb>"+fanart+"</thumb></fanart>"+chr(10)
		nfo+="	<thumb>"+cover+"</thumb>"+chr(10)
		nfo+="</tvshow>"+chr(10)
		
		fl = open(fs_enc(os.path.join(SaveDirectory, "tvshow.nfo")), "w")
		fl.write(nfo)
		fl.close()


def save_nfo(name, epd ,s , e, info={}):
		name=name.replace("/"," ").replace("\\"," ").replace("?","").replace(":","").replace('"',"").replace('*',"").replace('|',"").replace('>',"").replace('<',"").strip()
		epd=epd.replace("/"," ").replace("\\"," ").replace("?","").replace(":","").replace('"',"").replace('*',"").replace('|',"").replace('>',"").replace('<',"").strip()
		try: s=s.encode('utf-8')
		except: pass
		try: e=e.encode('utf-8')
		except: pass

		title="season "+s+" episode "+e
		title=s+" сезон "+e+" серия"
		#title=title.encode('utf-8')
		try: title=title.encode('utf-8')
		except: pass
		#name=ru(info['title'])
		cn=name.find(" (")
		if cn>0: name=name[:cn]
		
		try:title=xt(info['title'])
		except:pass
		
		try:plot=info['plot']
		except:plot=''
		try:cover=info['cover']
		except:cover=''
		try:fanart=info['fanart']
		except:fanart=''

		try:Directory= __settings__.getSetting("SaveDirectory2")
		except: Directory=os.path.join(addon.getAddonInfo('path'), 'strm')
		if Directory=="":Directory=os.path.join(addon.getAddonInfo('path'), 'strm')
		SaveDirectory = os.path.join(Directory, name)
		if os.path.isdir(fs_enc(SaveDirectory))==0: os.mkdir(fs_enc(SaveDirectory))
		
		nfo="<episodedetails>"+chr(10)
		nfo+="	<title>"+title+"</title>"+chr(10)
		nfo+="	<season>"+str(s)+"</season>"+chr(10)
		nfo+="	<episode>"+str(e)+"</episode>"+chr(10)
		nfo+="	<plot>"+plot+"</plot>"+chr(10)
		nfo+="	<fanart>"+fanart+"</fanart>"+chr(10)
		nfo+="	<thumb>"+cover+"</thumb>"+chr(10)
		nfo+="</episodedetails>"+chr(10)
		
		fl = open(fs_enc(os.path.join(SaveDirectory, epd+".nfo")), "w")
		fl.write(nfo)
		fl.close()


def save_purl(name, purl, info={}):
		epd='S00.E00'
		name=name.replace("/"," ").replace("\\"," ").replace("?","").replace(":","").replace('"',"").replace('*',"").replace('|',"").replace('>',"").replace('<',"").strip()
		epd=epd.replace("/"," ").replace("\\"," ").replace("?","").replace(":","").replace('"',"").replace('*',"").replace('|',"").replace('>',"").replace('<',"").strip()
		if isinstance(name, unicode): name=name.encode('utf-8')
		if isinstance(epd, unicode): epd=epd.encode('utf-8')
		
		try:Directory= __settings__.getSetting("SaveDirectory2")
		except: Directory=os.path.join(addon.getAddonInfo('path'), 'strm')
		if Directory=="":Directory=os.path.join(addon.getAddonInfo('path'), 'strm')
		
		SaveDirectory = os.path.join(Directory, name)
		
		if os.path.isdir(fs_enc(SaveDirectory))==0: os.mkdir(fs_enc(SaveDirectory))
		
		uri = construct_request({
			'purl': purl,
			'mode': 'run'
		})
		fl = open(fs_enc(os.path.join(SaveDirectory, epd+'.strm')), "w")
		fl.write(uri)
		fl.close()
		
		try:cover=info['cover']
		except:cover=''
		try:fanart=info['fanart']
		except:fanart=''

		nfo="<episodedetails>"+chr(10)
		nfo+="	<title>Открыть плагин</title>"+chr(10)
		nfo+="	<season>0</season>"+chr(10)
		nfo+="	<episode>0</episode>"+chr(10)
		nfo+="	<plot>Открыть плагин</plot>"+chr(10)
		nfo+="	<fanart>"+fanart+"</fanart>"+chr(10)
		nfo+="	<thumb>"+cover+"</thumb>"+chr(10)
		nfo+="</episodedetails>"+chr(10)
		
		fl = open(fs_enc(os.path.join(SaveDirectory, epd+".nfo")), "w")
		fl.write(nfo)
		fl.close()


class PICON_XML(xbmcgui.WindowXML):
	def __init__(self,strXMLname, strFallbackPath, strDefaultName, forceFallback):
		self.cid=__settings__.getSetting("picon_id")
		self.cnl=__settings__.getSetting("picon_cnl")
	
	def onInit(self):
		self.showList()
		self.setFocus(self.getControl(600))
	
	def showList(self):
		
		win = xbmcgui.Window (xbmcgui.getCurrentWindowId())
		#picon = pztv.get_picon(self.cid)
		title = self.cnl
		win.setProperty('title',  title)
		# передачи
		L=get_picons(title)
		list1=self.getControl(600)
		list1.reset()
		for i in L:
				title=i[i.rfind('/')+1:]
				item = xbmcgui.ListItem(title)
				item.setProperty('id', self.cid)
				item.setProperty('picon', i)
				list1.addItem(item)

	def onClick(self, controlID):
		
		if controlID == 600:
			list=self.getControl(controlID)
			listitem=list.getSelectedItem()
			id=listitem.getProperty('id')
			cp=os.path.join(pztv.Logo, id+'.png')
			cover=listitem.getProperty('picon')
			try:
				import urllib2
				req = urllib2.Request(url = cover, data = None)
				req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)')
				resp = urllib2.urlopen(req)
				fl = open(cp, "wb")
				fl.write(resp.read())
				fl.close()
			except: pass
			self.close()


class SAVE_XML(xbmcgui.WindowXML):
	def __init__(self,strXMLname, strFallbackPath, strDefaultName, forceFallback):
		pass
	
	def onInit(self):
		self.showList()
		self.setFocus(self.getControl(21))
	
	def showList(self):
		L=eval(__settings__.getSetting("saver_data"))['list']
		info = eval(__settings__.getSetting("saver_data"))['info']
		
		win = xbmcgui.Window (xbmcgui.getCurrentWindowId())
		
		ttl=__settings__.getSetting("save_title")
		if ttl=='': 
			try: 
				ttl=eval(__settings__.getSetting("saver_data"))['info']['originaltitle']
				__settings__.setSetting("save_title", ttl)
			except: 
				ttl=''
		win.setProperty('title', ttl)
		
		range_s=eval(__settings__.getSetting("range_s"))
		range_e=eval(__settings__.getSetting("range_e"))
		
		save_nfo=__settings__.getSetting("save_nfo")
		win.setProperty('nfo', save_nfo)
		if save_nfo == 'ДА': win.setProperty('vnfo', save_nfo)
		else: 				 win.setProperty('vnfo', '')
		
		try:genre=eval(__settings__.getSetting("saver_data"))['info']['genre']
		except: genre=''
		win.setProperty('genre', genre)
		
		try:cover=eval(__settings__.getSetting("saver_data"))['info']['cover']
		except: cover=''
		win.setProperty('cover', cover)
		
		try:fanart=eval(__settings__.getSetting("saver_data"))['info']['fanart']
		except: fanart=''
		win.setProperty('fanart', fanart)
		
		list1=self.getControl(500)
		list1.reset()
		n=0
		so=''
		ss=''
		ee=''
		for i in L:
				n+=1
				if range_s[0] == 't': s=range_s[1]
				else:                 s=i[range_s[0]:range_s[1]]
				
				if so!=s: n=1
				if range_e[0] == 'i': 
					if n<10: e='0'+str(n)
					else:	 e=str(n)
				else:
					e=i[range_e[0]:range_e[1]]
				
				if s not in ss: ss=ss+s+','
				ee=ee+e+','
				
				if media(i):
					title = ttl+".s"+rt(s)+".e"+rt(e)
					item = xbmcgui.ListItem(title)
					list1.addItem(item)
				so=s
		
		win.setProperty('s', ss)
		win.setProperty('e', ee)
		
	def onClick(self, controlID):
		print('onClick ' +str(controlID))
		if controlID == 1:
							save()
							self.close()
		if controlID == 2:  self.close()
		if controlID == 21: __settings__.setSetting("save_title", inputbox(__settings__.getSetting("save_title")))
		if controlID == 22: 
			sel = xbmcgui.Dialog()
			r = sel.select("Сезон:", ['Диапазон', 'Выбор'])
			if r == 0: 
				select('s')
			if r == 1: 
				ls=['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']
				sel = xbmcgui.Dialog()
				r = sel.select("Жанр:", ls)
				__settings__.setSetting("range_s", repr(['t',ls[r]]))
				
		if controlID == 23: 
			sel = xbmcgui.Dialog()
			r = sel.select("Сезон:", ['Диапазон', 'Счетчик'])
			if r == 0: select('e')
			if r == 1: __settings__.setSetting("range_e", repr(['i','01']))
				
		if controlID == 24:
			save_nfo=__settings__.getSetting("save_nfo")
			if save_nfo == 'ДА': __settings__.setSetting("save_nfo", "НЕТ")
			else: 				 __settings__.setSetting("save_nfo", "ДА")
		if controlID == 25:
			sel = xbmcgui.Dialog()
			r = sel.select("Жанр:", genres)
			value=genres[r]
			saver_data = eval(__settings__.getSetting("saver_data"))
			info = saver_data['info']
			info['genre']=value
			saver_data['info'] = info
			__settings__.setSetting("saver_data", repr(saver_data))
		if controlID == 26:
			ttl=__settings__.getSetting("save_title")
			if ttl=='': 
				try: 
					ttl=eval(__settings__.getSetting("saver_data"))['info']['originaltitle']
					__settings__.setSetting("save_title", ttl)
				except: 
					ttl=''
			ttl=rt(ttl)
			
			purl = 'plugin://plugin.video.tam/?mode=select_cover&name='+quote(ttl)
			xbmc.executebuiltin('ActivateWindow(10025,"'+purl+'", return)')
		self.showList()

class LIST_XML(xbmcgui.WindowXML):
	def __init__(self,strXMLname, strFallbackPath, strDefaultName, forceFallback):
		pass
	
	def onInit(self):
		self.showList()
		self.setFocus(self.getControl(1))
	
	def showList(self):
		L=eval(__settings__.getSetting("saver_data"))['list']
		info = eval(__settings__.getSetting("saver_data"))['info']
		
		win = xbmcgui.Window (xbmcgui.getCurrentWindowId())
		
		#win.setProperty('title', ttl)
		
		#save_nfo=__settings__.getSetting("save_nfo")
		#win.setProperty('nfo', save_nfo)
		#if save_nfo == 'ДА': win.setProperty('vnfo', save_nfo)
		#else: 				 win.setProperty('vnfo', '')
		
		try:genre=eval(__settings__.getSetting("saver_data"))['info']['genre']
		except: genre=''
		win.setProperty('genre', genre)
		
		try:cover=eval(__settings__.getSetting("saver_data"))['info']['cover']
		except: cover=''
		win.setProperty('cover', cover)
		
		try:fanart=eval(__settings__.getSetting("saver_data"))['info']['fanart']
		except: fanart=''
		win.setProperty('fanart', fanart)
		
		list1=self.getControl(500)
		list1.reset()
		n=0
		
		for i in L:
				n+=1
				title = ''
				item = xbmcgui.ListItem(title)
				for p in i.keys():
					item.setProperty(p, i[p])
				list1.addItem(item)
		
	def onClick(self, controlID):
		print('onClick ' +str(controlID))
		if controlID == 1:
							save()
							self.close()
		if controlID == 2:  self.close()
		if controlID == 21: __settings__.setSetting("save_title", inputbox(__settings__.getSetting("save_title")))
		if controlID == 22: 
			sel = xbmcgui.Dialog()
			r = sel.select("Сезон:", ['Диапазон', 'Выбор'])
			if r == 0: 
				select('s')
			if r == 1: 
				ls=['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']
				sel = xbmcgui.Dialog()
				r = sel.select("Жанр:", ls)
				__settings__.setSetting("range_s", repr(['t',ls[r]]))
				
		if controlID == 23: 
			sel = xbmcgui.Dialog()
			r = sel.select("Сезон:", ['Диапазон', 'Счетчик'])
			if r == 0: select('e')
			if r == 1: __settings__.setSetting("range_e", repr(['i','01']))
				
		if controlID == 24:
			save_nfo=__settings__.getSetting("save_nfo")
			if save_nfo == 'ДА': __settings__.setSetting("save_nfo", "НЕТ")
			else: 				 __settings__.setSetting("save_nfo", "ДА")
		if controlID == 25:
			sel = xbmcgui.Dialog()
			r = sel.select("Жанр:", genres)
			value=genres[r]
			saver_data = eval(__settings__.getSetting("saver_data"))
			info = saver_data['info']
			info['genre']=value
			saver_data['info'] = info
			__settings__.setSetting("saver_data", repr(saver_data))
		if controlID == 26:
			ttl=__settings__.getSetting("save_title")
			if ttl=='': 
				try: 
					ttl=eval(__settings__.getSetting("saver_data"))['info']['originaltitle']
					__settings__.setSetting("save_title", ttl)
				except: 
					ttl=''
			ttl=rt(ttl)
			
			purl = 'plugin://plugin.video.tam/?mode=select_cover&name='+quote(ttl)
			xbmc.executebuiltin('ActivateWindow(10025,"'+purl+'", return)')
		self.showList()

class SELECT_XML(xbmcgui.WindowXMLDialog):
	def __init__(self,strXMLname, strFallbackPath, strDefaultName, forceFallback):
		self.item_name = eval(__settings__.getSetting("saver_data"))['list'][0]
		self.item_type=__settings__.getSetting("item_type")
	
	def onInit(self):
		self.showList()
		self.setFocus(self.getControl(500))
	
	def showList(self):
		win = xbmcgui.Window (xbmcgui.getCurrentWindowId())
		
		#L='Verry_Long_string_Example_title.S01.E02_reliser_year_rip.mkv'
		list1=self.getControl(500)
		list1.reset()
		list2=self.getControl(600)
		list2.reset()

		for i in self.item_name:
				item = xbmcgui.ListItem(i)
				list2.addItem(item)
				
		for i in self.item_name:
				item = xbmcgui.ListItem(i)
				list1.addItem(item)

	def onClick(self, controlID):
		print('onClick ' +str(controlID))
		if controlID == 500:
			self.setFocus(self.getControl(600))
		if controlID == 600:
			self.setFocus(self.getControl(1))
		if controlID == 2: 
			self.close()
		if controlID == 1: 
			list1=self.getControl(500)
			list2=self.getControl(600)
			pos1 = list1.getSelectedPosition()
			pos2 = list2.getSelectedPosition()
			if pos1<pos2: r=[pos1,pos2+1]
			else: r=[pos2,pos1+1]
			__settings__.setSetting(self.item_type, repr(r))
			self.close()


class OPEN_XML(xbmcgui.WindowXMLDialog):
	def __init__(self,strXMLname, strFallbackPath, strDefaultName, forceFallback):
		#self.item_name = eval(__settings__.getSetting("saver_data"))['list'][0]
		#self.item_type=__settings__.getSetting("item_type")
		self.progressBar = xbmcgui.DialogProgress()
		self.progressBar.create('ТАМ', 'Запуск сохраненного файла')
		
		pass
	
	def onInit(self):
		self.setFocus(self.getControl(2))
		self.showList()
	
	def showList(self):
		__settings__.setSetting("break_play", 'false')
		win = xbmcgui.Window (xbmcgui.getCurrentWindowId())
		try:self.getControl(32).setLabel(eval(__settings__.getSetting("saver_data"))['name'])
		except: self.getControl(32).setLabel('Запуск')
		
		for i in range(0,4):
			lbl=self.getControl(31)
			lbl.setLabel(str(4-i))
			xbmc.sleep(900)
		url=eval(__settings__.getSetting("saver_data"))['url']
		self.close()
	
	def onClick(self, controlID):
		print('onClick ' +str(controlID))
		if controlID == 2:
			self.progressBar.close()
			#xbmc.Player().stop()
			__settings__.setSetting("break_play", 'true')
			xbmcplugin.endOfDirectory(int(sys.argv[1]), False, False)
			self.close()
		if controlID == 1:
			self.progressBar.close()
			#xbmc.Player().stop()
			#xbmcplugin.endOfDirectory(int(sys.argv[1]), False, False)
			__settings__.setSetting("break_play", 'true')
			purl=eval(__settings__.getSetting("saver_data"))['purl']
			xbmc.executebuiltin('Dialog.Close(all,true)')
			xbmc.executebuiltin('ActivateWindow(10025,"'+purl+'", return)')
			xbmc.executebuiltin("Container.Refresh()")
			self.close()
		if controlID == 24:
			self.progressBar.close()
			#xbmc.Player().stop()
			#xbmcplugin.endOfDirectory(int(sys.argv[1]), False, False)
			__settings__.setSetting("break_play", 'true')
			title=eval(__settings__.getSetting("saver_data"))['name']
			xbmc.executebuiltin('Dialog.Close(all,true)')
			if title!='': xbmc.executebuiltin('ActivateWindow(10025,"plugin://plugin.video.KinoPoisk.ru/?mode=HSearch&url='+title+'", return)')
			#xbmc.executebuiltin("Container.Refresh()")
			self.close()


def open_strm():
	
	#skin = "Default"
	init()
	ui = OPEN_XML("open.xml", addon.getAddonInfo('path'), skin, "720p")
	ui.doModal()
	del ui
	
	
	return __settings__.getSetting("break_play")

def main(data):
	#skin = "Default"
	init(data)
	ui = SAVE_XML("main.xml", addon.getAddonInfo('path'), skin, "720p")
	ui.doModal()
	del ui

def select(t):
	__settings__.setSetting("item_type", 'range_'+t)
	ui = SELECT_XML("range.xml", addon.getAddonInfo('path'), skin, "720p")
	ui.doModal()
	del ui

def open_list():
	ui = LIST_XML("list.xml", addon.getAddonInfo('path'), skin, "720p")
	ui.doModal()
	del ui

def init(saver_data={}):
	
	if saver_data=={}: saver_data = eval(__settings__.getSetting("saver_data"))
	try:ttl=saver_data['info']['originaltitle']
	except: ttl=''

	__settings__.setSetting("save_title", ttl)
	
	try:t=saver_data['list'][0]
	except: t=''
	st=find_s(t)
	if st==-1: __settings__.setSetting("range_s", repr([0,0]))
	else:      __settings__.setSetting("range_s", repr([st,st+2]))
	
	e=find_e(t)
	if e==-1: __settings__.setSetting("range_e", repr([0,0]))
	else:     __settings__.setSetting("range_e", repr([e,e+2]))
	
	__settings__.setSetting("save_nfo", 'НЕТ')
#xbmcplugin.endOfDirectory(handle, False, False)
#main()
