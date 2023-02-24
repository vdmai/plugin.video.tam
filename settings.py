# -*- coding: utf-8 -*-
import os
try:
	import xbmcaddon, xbmc, xbmcvfs
	addon = xbmcaddon.Addon(id='plugin.video.tam')
	set=xbmcaddon.Addon(id='plugin.video.tam')
	set.setSetting("plugin.video.tam",'3')
	#db_dir = os.path.join(addon.getAddonInfo('path'),"settings")
	try:    db_dir = os.path.join(xbmc.translatePath("special://masterprofile/"),"addon_data","plugin.video.tam")
	except: db_dir = os.path.join(xbmcvfs.translatePath("special://masterprofile/"),"addon_data","plugin.video.tam")
except:
	db_dir = os.path.join(os.getcwd(), "settings" )

def set(key, val):
	try:
		fp=os.path.join(db_dir, key)
		fl = open(fp, "w")
		fl.write(repr(val))
		fl.close()
		return 'ok'
	except:
		return 'error set '+key

def get(key):
	try:
		fp=os.path.join(db_dir, key)
		fl = open(fp, "r")
		t=fl.read()
		fl.close()
		return eval(t)
	except:
		val=default(key)
		if val!='': set(key, val)
		return val

def default(key):
		return ''

def rem(key):
	fp=os.path.join(db_dir, key)
	os.remove(fp)
	
def keys(key):
	L=[]
	for i in os.listdir(db_dir):
		if key in i: L.append(i)
	return L
#print set('KEY', 'VALUE')
#print get('KEY')
