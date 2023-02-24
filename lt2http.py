# -*- coding: utf-8 -*-
import sys
import json
import socket
import threading
PY2 = sys.version_info.major == 2
if PY2:
       from urllib2 import HTTPError, URLError, HTTPRedirectHandler, Request, urlopen, HTTPHandler, build_opener
       from urllib import urlencode
else:
       from urllib.parse import urlencode
       from urllib.error import HTTPError, URLError
       from urllib.request import HTTPRedirectHandler, Request, urlopen, HTTPHandler, build_opener


LT2HTTP_HOST = "http://127.0.0.1:65225"
LT2HTTP_LIST = 0

def Init():
    try:
        import xbmcaddon
        global LT2HTTP_HOST, LT2HTTP_LIST
        addon = xbmcaddon.Addon()
        LT2HTTP_HOST = "http://"+addon.getSetting("lt_serv")+':'+addon.getSetting("lt_port")
        LT2HTTP_LIST = int(addon.getSetting("lt_list"))
    except: pass

Init()

class closing(object):
    def __init__(self, thing):
        self.thing = thing

    def __enter__(self):
        return self.thing

    def __exit__(self, *exc_info):
        self.thing.close()


class NoRedirectHandler(HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        import urllib
        infourl = urllib.addinfourl(fp, headers, headers["Location"])
        infourl.status = code
        infourl.code = code
        return infourl

    http_error_300 = http_error_302
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302


def client(url, post_data=None, get_data=None, raw=False, host=None, ljs=True, err=False):
    socket.setdefaulttimeout(30)
    if get_data:
        url += '?' + urlencode(get_data)
    if post_data and raw:
        post_data = post_data
    elif post_data:
        try:
            post_data = json.dumps(post_data)
            if not PY2: post_data = post_data.encode('utf8')
        except:
            post_data = {"": ""}
    if host:
        url = host + url
    else:
        url = LT2HTTP_HOST+url
    req = Request(url, post_data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Accept-Charset', 'utf-8')
    req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:21.0) Gecko/20100101 Firefox/21.0')

    try:
        with closing(urlopen(req)) as response:
            payload = response.read()

            try:
                if payload and ljs:
                    return json.loads(payload.decode('utf-8', 'replace'))
                else:
                    return payload
            except:
                return payload
    except HTTPError as e:
        print(e)
        errlines = e.readlines()
        print(errlines)
        print(e.code)
        print(e.reason)
        print(e.args)
        if err:
               rete = {'e.code':e.code, 'e.reason': e.reason, 'e.args': e.args, 'e':e}
               if errlines and len(errlines) > 0:
                    rete.update(json.loads(errlines[0].decode('utf-8', 'replace')))
               return rete
        return None
    except URLError as e:
        print(e)
        print(e.args)
        print(e.reason)
        if err: return {'e.reason': e.reason, 'e.args': e.args, 'e':e}
        return None
    except Exception as e:
        print(e)
        if err: return {'e':e}
        return None

class MyHandler(HTTPHandler):
    def http_response(self, req, response):
        return response


def touch(url):
    o = build_opener(MyHandler())
    t = threading.Thread(target=o.open, args=(url,))
    t.start()


def addTorrent(uri, err=False):
    return client('/service/add/uri', get_data={'uri': uri}, err=err)

def torrentsList():
    return client('/torrents')

def filesList(hash, err=False):
    return client('/torrents/'+str(hash)+'/files', err=err)

def removeTorrent(hash, err=False):
    return client('/torrents/'+str(hash)+'/remove', err=err)

def statusTorrent(hash, err=False):
    return client('/torrents/'+str(hash)+'/status', err=err)

def infoTorrent(hash, err=False):
    return client('/torrents/'+str(hash)+'/info', err=err)

def statusFile(hash, id, err=False):
    return client('/torrents/'+str(hash)+'/files/'+str(id)+'/status', err=err)

def stopFile(hash, id, err=False):
    return client('/torrents/'+str(hash)+'/files/'+str(id)+'/stop', err=err)

def getStreamUri(hash, id):
    for i in filesList(hash):
       if i['id'] == int(id): return i['stream']
    return None

def startBuffering(hash, id):
    touch(LT2HTTP_HOST+'/torrents/'+str(hash)+'/files/'+str(id)+'/download?buffer=true')

def removeUnusedTorrentsFromList(hash, remh=True):
    tlist = torrentsList()
    if not tlist: return
    lid = -1
    for i in range(len(tlist)):
        if tlist[i]['hash'] == str(hash):
             lid = i
             break
    if lid > -1: del tlist[lid]
    len_tlist = len(tlist)
    if len_tlist == 0:
        if LT2HTTP_LIST == 0 and remh: removeTorrent(hash)
        return
    len_tlist += 1
    if not remh and LT2HTTP_LIST ==0: len_tlist -= 1
    if len_tlist > LT2HTTP_LIST:
        for i in range(len_tlist-LT2HTTP_LIST):
             removeTorrent(tlist[i]['hash'])


def files_list(url, rem=True, err=False):
    import xbmc
    lt_s = addTorrent(url, True)
    if not lt_s.get('success'):
           err = lt_s.get('error', '')
           if 'hash' in err and 'already exists' in err:
                   hash = err.split("'")[1]
                   lt_s = infoTorrent(hash, True)
           else:
                 if err: return lt_s
                 return
    if lt_s.get('hash'):
          if not lt_s['has_metadata']:
                for i in range(20):
                           xbmc.sleep(500)
                           lt_s2 = infoTorrent(lt_s['hash'])
                           if lt_s2.get('has_metadata'): break
                           if i == 19: return
          ret = filesList(lt_s['hash'])
          if rem:
                xbmc.sleep(1000)
                removeTorrent(lt_s['hash'])
          return ret

def Play(url, ind, xplayer=None):
    import xbmcgui, xbmc, xbmcplugin
    def abortRequested():
        if sys.version_info.major > 2: return xbmc.Monitor().abortRequested()
        return xbmc.abortRequested
    progressBar = xbmcgui.DialogProgress()
    progressBar.create('lt2http', 'Запуск')
    lt_s = addTorrent(url, True)
    status = -1
    if not lt_s.get('success'):
           err = lt_s.get('error', '')
           if 'hash' in err and 'already exists' in err:
                  hash = err.split("'")[1]
                  lt_s = infoTorrent(hash, True)
                  status = statusTorrent(hash, True).get('status', -1)

    if lt_s.get('hash'):
           if not lt_s['has_metadata']:
                  for i in range(60):
                         #progressBar.update(i, 'Получение инфо...')
                         xbmc.sleep(1000)
                         lt_s2 = infoTorrent(lt_s['hash'])
                         if lt_s2.get('has_metadata'): break
                         if i == 59:
                                 progressBar.close()
                                 return
           global LT2HASH
           LT2HASH = lt_s['hash']
           uri = getStreamUri(LT2HASH, ind)
           is_memory = infoTorrent(LT2HASH).get('is_memory_storage')
    else:
          err = lt_s.get('error','') + '[CR]' + str(lt_s.get('e.reason', ''))
          progressBar.update(0, 'Ошибка открытия:[CR]'+err)
          xbmc.sleep(2000)
          progressBar.close()
          return


    plb = False
    if status < 0: startBuffering(LT2HASH, ind)
    last_buf_progress = 0
    for i in range(60):
                xbmc.sleep(1000)
                i = statusTorrent(LT2HASH)
                try: seeds=i["seeders"]
                except: seeds=0
                try: speed=int(i["download_rate"]/1024)
                except: speed=0
                try: progress=int(i["progress"]*100)
                except: progress=0
                try: download=int(i["total_download"]/1024/1024)
                except: download=0

                f = statusFile(LT2HASH, ind)
                try: buf_progress=int(f['buffering_progress'])
                except: buf_progress = 0

                if buf_progress > 0 and last_buf_progress < buf_progress or buf_progress >= 100:
                         progress = buf_progress
                         last_buf_progress = buf_progress

                try:progressBar.update(int(progress), 'Предварительная буферизация: '+str(download)+" MB", "Сиды: "+str(seeds), "Скорость: "+str(speed)+' Kbit/s')
                except:progressBar.update(int(progress), 'Предварительная буферизация: '+str(download)+" MB \nСиды: "+str(seeds)+" \nСкорость: "+str(speed)+' Kbit/s')

                if progressBar.iscanceled() or abortRequested() or not i:
                            progressBar.update(0)
                            progressBar.close()
                            #lt2h.stopFile(lt_s['hash'], ind)
                            #lt2h.removeTorrent(lt_s['hash'])
                            removeUnusedTorrentsFromList(lt_s['hash'])
                            return

                if is_memory and (progress>=100 or buf_progress>=100):
                     plb = True
                     break

                if not is_memory and (buf_progress >= 100 or download > 64):
                     plb = True
                     break

    progressBar.update(0)
    progressBar.close()
    if plb:

        removeUnusedTorrentsFromList(lt_s['hash'], False)

        if xplayer: Player=xplayer
        item = xbmcgui.ListItem(path=uri)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    else:
        #lt2h.stopFile(lt_s['hash'], ind)
        #lt2h.removeTorrent(lt_s['hash'])
        removeUnusedTorrentsFromList(lt_s['hash'])
        return

    while not abortRequested() and not xbmc.Player().isPlaying():
           xbmc.sleep(100)

    while not abortRequested() and xbmc.Player().isPlaying():
           xbmc.sleep(500)
    #xbmcgui.Dialog().textviewer('Finish', 'test!')
    #lt2h.stopFile(lt_s['hash'], ind)
    removeUnusedTorrentsFromList(lt_s['hash'])
    #lt2h.removeTorrent(lt_s['hash'])
    return lt_s['hash']


def status_string(hash=None):
    if not hash: hash=LT2HASH
    i = statusTorrent(hash, True)
    try:
        seeds=i["seeders"]
        speed=int(i["download_rate"]/1024)
        up_speed=int(i["upload_rate"]/1024)
        progress=int(i["progress"]*100)
        download=int(i["total_download"]/1024/1024)
#		try:
#			size = int(i['FileStats'][FID]['Length'])
#			progress= int(float(download) * 100 / size)
#		except:
#			size = 0
#			progress = 0
        return "Загружено: "+str(download)+" MB ("+str(progress)+" %) \nСиды: "+str(seeds)+" \nСкорость загрузки: "+str(speed)+' Kbit/s'+" Скорость отдачи: "+str(up_speed)+' Kbit/s'
    except:
        return 'err' #str(i)


if __name__ == "__main__" :
    import time

    print('test!')

    for t in torrentsList():
         print(removeTorrent(t['hash']))

    time.sleep(2)

    print(client('/info'))

    t = addTorrent('http://rutor.lib/download/826379', err=True)
#    t = addTorrent('magnet:?xt=urn:btih:')
#    t = {'hash':''}

    print(t)

    print(torrentsList())

    if t:
          print(filesList(t['hash'])[0])
          print(getStreamUri(t['hash'], 0))
          print(statusTorrent(t['hash']))
          print(infoTorrent(t['hash']))
          startBuffering(t['hash'], 0)
          print(statusFile(t['hash'], 0))
    if t:
          while statusTorrent(t['hash']).get('progress', 0) < 1:
#             print(statusTorrent(t['hash']))
             print(statusFile(t['hash'], 0))
             time.sleep(1)

    time.sleep(2)
    if t:
          LT2HTTP_LIST = 0
          removeUnusedTorrentsFromList(t['hash'])

    print('List',torrentsList())

    for t in torrentsList():
         print(removeTorrent(t['hash']))

#    print(infoTorrent('a21df', True))
