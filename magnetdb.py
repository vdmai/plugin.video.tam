# -*- coding: utf-8 -*-
import sys, os, json
from ftplib import FTP
temp_dir = "d:\\"

if sys.version_info.major > 2:  # Python 3 or later
	import urllib.request
	from urllib.parse import quote
	from urllib.parse import unquote
	import urllib.request as urllib2
else:  # Python 2
	import urllib, urlparse
	from urllib import quote
	from urllib import unquote
	import urllib2

null = ''
false = False
true = True

def d2j(d):
	j=json.dumps(d, ensure_ascii=False)
	return j

def ru(x):return unicode(x,'utf8', 'ignore')

def getURL(url,Referer = 'http://emulations.ru/'):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Opera/10.60 (X11; openSUSE 11.3/Linux i686; U; ru) Presto/2.6.30 Version/10.60')
	req.add_header('Accept', 'text/html, application/xml, application/xhtml+xml, */*')
	req.add_header('Accept-Language', 'ru,en;q=0.9')
	req.add_header('Referer', Referer)
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	return link

def mfindal(http, ss, es):
	L=[]
	while http.find(es)>0:
		s=http.find(ss)
		#sn=http[s:]
		e=http.find(es)
		i=http[s:e]
		L.append(i)
		http=http[e+2:]
	return L

def mfind(t,s,e):
	r=t[t.find(s)+len(s):]
	r2=r[:r.find(e)]
	return r2

def CRC32(buf):
		import binascii
		buf = (binascii.crc32(buf) & 0xFFFFFFFF)
		return str("%08X" % buf)

def save_inf(s):
	p = os.path.join(ru(temp_dir),"temp.txt")
	f = open(p, "w")
	f.write(s)
	f.close()
	return p

def upload(ftp, path, ftp_path):
	with open(path, 'rb') as fobj:
		ftp.storbinary('STOR ' + ftp_path, fobj, 1024)


def get_path(id):
	s=[id[0],id[1:3],id[3:6]]
	#print s
	return s

def make_id(ftp, id):
	s=''
	for c in get_path(id):
		s+='/'+c
		try:ftp.mkd(s)
		except: pass
	ret=s+'.info'
	#print ret
	return ret

def verifid_id(ftp, id):
	s=''
	for c in get_path(id):
		s+='/'+c
	try:size=ftp.size(s+'.info')
	except: size=0
	#print size
	return size



def add(info):
	return add_compression_info(info)


def add2(info):
	id=info['id']
	HUP=get_host(id)
	HOST=HUP['HOST']
	USER=HUP['USER']
	PASS=HUP['PASS']
	ftp = FTP(HOST)
	ftp.login(USER, PASS)
	print ('ADD DB: '+id)
	if verifid_id(ftp, id) == 0:
		dir=make_id(ftp, id)
		path = save_inf(repr(info))
		upload(ftp, path, dir+'.info')
	ftp.quit()

def update(info):
	return add_compression_info(info)

def get_info(id):
	return get_compression_info(id)

def get_host(id):
	return {'HOST':'roms.my1.ru', 'USER':'5roms', 'PASS':'19111980'}


def make_compression_info(id):
	#print 'make_compression_info'
	c=get_path(id)
	HUP=get_host(id)
	HOST=HUP['HOST']
	USER=HUP['USER']
	PASS=HUP['PASS']
	cinfo={}
	
	ftp = FTP(HOST)
	ftp.login(USER, PASS)
	print ('ADD DB: '+id)
	
	make_id(ftp, id)
	
	path = save_inf(repr(cinfo))
	url='/'+c[0]+'/'+c[1]+'/'+c[2]+'/'+id[6:8]+'.info'
	upload(ftp, path, url)
	ftp.quit()
	return cinfo

def get_compression_info(id):
	#print get_compression_info
	c=get_path(id)
	HOST=get_host(id)['HOST']
	url='http://'+HOST+'/'+c[0]+'/'+c[1]+'/'+c[2]+'/'+id[6:8]+'.info'
	#print url
	try: 
		cinfo=eval(getURL(url))
		#print 'cinfo найден'
	except: 
		#cinfo=make_compression_info(id)
		pass
		#print 'cinfo создан'
	info=cinfo[id]
	return info

def add_compression_info(nfo):
	id=nfo['id']
	c=get_path(id)
	HUP=get_host(id)
	HOST=HUP['HOST']
	USER=HUP['USER']
	PASS=HUP['PASS']
	url='http://'+HOST+'/'+c[0]+'/'+c[1]+'/'+c[2]+'/'+id[6:8]+'.info'
	print (url)
	try: cinfo=eval(getURL(url))
	except: cinfo=make_compression_info(id)
	cinfo[id]=nfo
	
	ftp = FTP(HOST)
	ftp.login(USER, PASS)
	#print 'SAVEcomp KinoDB: '+id
	#dir=make_id(ftp, id)
	path = save_inf(d2j(cinfo))
	ftp_url='/'+c[0]+'/'+c[1]+'/'+c[2]+'/'+id[6:8]+'.info'
	upload(ftp, path, ftp_url)
	ftp.quit()

#print get_compression_info('445')
#print get_path('1111911')

#add_compression_info({'id':'16378f92db90d9129cade6bc26ce01c27dd1ef034', 'list':['1','2']})
#print get_compression_info('6378f92db90d9129cade6bc26ce01c27dd1ef034')