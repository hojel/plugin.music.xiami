# -*- coding: utf-8 -*-
# http://www.xiami.com/

#   /chart/data?c=101&type=[0-4]&page=1&limit=25
#      type/[0-4] - [all|huayu|oumei|ri|han]

#   /[artist|album]/index/c/[1-2]/type/[0-3]
#      c/1 - Popular
#      c/2 - Recommended

from xbmcswift2 import Plugin, actions

plugin = Plugin()
_L = plugin.get_string

import urllib, urllib2
from BeautifulSoup import BeautifulSoup
import simplejson
import re

root_url = "http://www.xiami.com"
agent_str = "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.17 Safari/537.36"

tPrevPage = u"[B]<<[/B]%s" % _L(30000)
tNextPage = u"%s[B]>>[/B]" % _L(30001)

def unescape_name(s):
    return s.replace('&#039;',"'")

@plugin.route('/')
def main_menu():
    items = [
        {'label':_L(30018), 'path':plugin.url_for('bang_albums_menu', type='new')},
        {'label':_L(30019), 'path':plugin.url_for('bang_albums_menu', type='hot')},
        {'label':_L(30025), 'path':plugin.url_for('chart_menu')},
        {'label':_L(30010), 'path':plugin.url_for('search', domain='artist')},
        {'label':_L(30011), 'path':plugin.url_for('search', domain='album')},
        {'label':_L(30017), 'path':plugin.url_for('jump_menu')},
    ]
    return items

@plugin.route('/bang-albums/<type>')
def bang_albums_menu(type):
    items = [
        {'label':_L(30020), 'path':plugin.url_for('bang_albums', type=type, style='all')},
        {'label':_L(30021), 'path':plugin.url_for('bang_albums', type=type, style='huayu')},
        {'label':_L(30022), 'path':plugin.url_for('bang_albums', type=type, style='oumei')},
        {'label':_L(30023), 'path':plugin.url_for('bang_albums', type=type, style='ri')},
        {'label':_L(30024), 'path':plugin.url_for('bang_albums', type=type, style='han')},
    ]
    return items

@plugin.route('/bang-albums/<type>/<style>')
def bang_albums(type, style):
    url = root_url+'/web/bang-albums?type=%s&style=%s' % (type, style)
    plugin.log.debug(url)
    req = urllib2.Request(url, None, {'User-Agent':agent_str})
    content = urllib2.urlopen(req, timeout=5).read()
    data = simplejson.loads(content)

    result = []
    for item in data['albums']:
        title = unescape_name(item['album_name'])
    	result.append({
            'label': title,
            'label2': item['artist_name'],
            'path': plugin.url_for('album', albumid=item['album_id']),
            'thumbnail': item['logo'],
            'context_menu': [
                (_L(30100), actions.update_view(plugin.url_for('artist_top', artistid=item['artist_id']))),
            ]
        })
    return plugin.finish(result, view_mode='thumbnail')

@plugin.route('/chart_top')
def chart_menu():
    items = [
        {'label':_L(30020), 'path':plugin.url_for('chart', type='all')},
        {'label':_L(30021), 'path':plugin.url_for('chart', type='huayu')},
        {'label':_L(30022), 'path':plugin.url_for('chart', type='oumei')},
        {'label':_L(30026), 'path':plugin.url_for('chart', type='rihan')},
        #
        {'label':_L(30027), 'path':plugin.url_for('chart', type='billboard')},
        {'label':_L(30028), 'path':plugin.url_for('chart', type='uk')},
        {'label':_L(30029), 'path':plugin.url_for('chart', type='oricon')},
        {'label':_L(30030), 'path':plugin.url_for('chart', type='mnet')},
    ]
    return items

@plugin.route('/chart/<type>')
def chart(type):
    url = root_url+'/web/get-songs?type=%s&rtype=bang&id=0' % type
    plugin.log.debug(url)
    print url
    req = urllib2.Request(url, None, {'User-Agent':agent_str})
    content = urllib2.urlopen(req, timeout=5).read()
    data = simplejson.loads(content)

    result = []
    for item in data['data']:
        title = unescape_name(item['title'])
        thumb = item['cover']
        thumb = thumb[ thumb.rfind('http://') : ]
    	result.append({
            'label': title,
            'path': item['src'],
            'thumbnail': thumb,
            'is_playable': True,
        })
    return result

@plugin.route('/search/<domain>')
def search(domain):
    keywd = plugin.keyboard(heading='Keyword')

    url = root_url+"/search/%s?key=%s" % (domain, urllib.quote_plus(keywd))

    req = urllib2.Request(url, None, {'User-Agent':agent_str})
    content = urllib2.urlopen(req, timeout=5).read()
    html = BeautifulSoup(content)
    result = []
    for item in html.find('div', {'class':re.compile('Block_list')}).findAll('li'):
        title = ''.join(item.find('p', {'class':'name'}).findAll(text=True))
        thumb = item.find('img')['src']
        if domain == 'artist':
            url = item.find('a', {'class':'artist100'})['href']
            artistid = url.split('/')[-1]
            result.append({
                'label': title,
                'path': plugin.url_for('artist_top', artistid=artistid),
                'thumbnail': thumb,
                'context_menu': [
                    (_L(30103), actions.update_view(plugin.url_for('topsongs', artistid=artistid))),
                    (_L(30104), actions.update_view(plugin.url_for('similar_artists', artistid=artistid))),
                ]
            })
        elif domain == 'album':
            url = item.find('a', {'class':'CDcover100'})['href']
            albumid = url.split('/')[-1]
            url = item.find('a', {'class':'singer'})['href']
            artistid = url.split('/')[-1]
            result.append({
                'label': title,
                'path': plugin.url_for('album', albumid=albumid),
                'thumbnail': thumb,
                'context_menu': [
                    (_L(30100), actions.update_view(plugin.url_for('artist_top', artistid=artistid))),
                ]
            })
    return plugin.finish(result, view_mode='thumbnail')

@plugin.route('/jump_top')
def jump_menu():
    items = [
        {'label':_L(30014), 'path':plugin.url_for('artist_input')},
        {'label':_L(30015), 'path':plugin.url_for('album_input')},
        {'label':_L(30016), 'path':plugin.url_for('collect_input')},
    ]
    return items

@plugin.route('/jump/artist')
def artist_input():
    id = plugin.keyboard(heading='Artist ID')
    return plugin.redirect( plugin.url_for('artist_top', artistid=id) )

@plugin.route('/jump/album')
def album_input():
    id = plugin.keyboard(heading='Album ID')
    return plugin.redirect( plugin.url_for('album', albumid=id) )

@plugin.route('/jump/collect')
def collect_input():
    id = plugin.keyboard(heading='Collect ID')
    return plugin.redirect( plugin.url_for('collect', collectid=id) )

@plugin.route('/artist/<artistid>')
def artist_top(artistid):
    # artist info
    url = root_url+'/app/android/artist?id='+artistid
    req = urllib2.Request(url, None, {'User-Agent':agent_str})
    content = urllib2.urlopen(req, timeout=5).read()
    data = simplejson.loads(content)
    albums_count = data['artist']['albums_count']

    plugin.redirect( plugin.url_for('artist', artistid=artistid, albumscnt=albums_count, page='0') )

@plugin.route('/artist/<artistid>/<albumscnt>/<page>')
def artist(artistid, albumscnt, page):
    albums_count = int(albumscnt)
    pageN = 1 if page == '0' else int(page)

    # discography
    url = root_url+'/app/android/artist-albums?id=%s&page=%d' % (artistid, pageN)
    plugin.log.debug(url)

    req = urllib2.Request(url, None, {'User-Agent':agent_str})
    content = urllib2.urlopen(req, timeout=5).read()
    data = simplejson.loads(content)
    result = []
    for item in data['albums']:
        title = unescape_name(item['title'])
        result.append({
            'label': title,
            'path': plugin.url_for('album', albumid=item['album_id']),
            'thumbnail': item['album_logo'],
        })

    # navigation
    if pageN > 1:
        result.append({
            'label': tPrevPage,
            'path': plugin.url_for('artist', artistid=artistid, albumscnt=albumscnt, page=pageN-1)
        })
    if (pageN*20) < albums_count:
        result.append({
            'label': tNextPage,
            'path': plugin.url_for('artist', artistid=artistid, albumscnt=albumscnt, page=pageN+1)
        })
    morepage = False if page == '0' else True
    return plugin.finish(result, update_listing=morepage, view_mode='thumbnail')

@plugin.route('/album/<albumid>')
def album(albumid):
    # album info
    url = root_url+'/app/android/album?id='+albumid

    req = urllib2.Request(url, None, {'User-Agent':agent_str})
    content = urllib2.urlopen(req, timeout=5).read()
    data = simplejson.loads(content)
    result = []
    for item in data['album']['songs']:
        title = unescape_name(item['name'])
        result.append({
            'label': title,
            'path': item['location'],
            'info': {'type':'music', 'infoLabels':{'tracknumber':int(item['track']),'title':title}},
            'thumbnail': item['album_logo'],
            'is_playable': True,
            'context_menu': [
                (_L(30100), actions.update_view(plugin.url_for('artist_top', artistid=item['artist_id']))),
                (_L(30102), actions.background(plugin.url_for('download_file', url=item['location']))),
            ]
        })
    return result

@plugin.route('/collect/<collectid>')
def collect(collectid):
    #url = root_url+'/song/playlist/id/%s/type/3' % collectid
    url = root_url+'/app/android/collect?id=%s' % collectid
    req = urllib2.Request(url, None, {'User-Agent':agent_str})
    content = urllib2.urlopen(req, timeout=5).read()
    data = simplejson.loads(content)
    result = []
    for item in data['collect']['songs']:
        title = unescape_name(item['name'])
        result.append({
            'label': title,
            'label2': item['artist_name'],
            'path': item['location'],
            'info': {'type':'music', 'infoLabels':{'title':title,'album':item['title'],'artist':item['artist_name']}},
            'thumbnail': item['album_logo'],
            'is_playable': True,
            'context_menu': [
                (_L(30100), actions.update_view(plugin.url_for('artist_top', artistid=item['artist_id']))),
                (_L(30101), actions.update_view(plugin.url_for('album', albumid=item['album_id']))),
                (_L(30102), actions.background(plugin.url_for('download_file', url=item['location']))),
            ]
        })
    return plugin.finish(result, view_mode='thumbnail')

@plugin.route('/topsongs/<artistid>')
def topsongs(artistid):
    url = root_url+'/app/android/artist-topsongs?id='+artistid

    req = urllib2.Request(url, None, {'User-Agent':agent_str})
    content = urllib2.urlopen(req, timeout=5).read()
    data = simplejson.loads(content)
    result = []
    for item in data['songs']:
        title = unescape_name(item['name'])
        result.append({
            'label': title,
            'path': item['location'],
            'info': {'type':'music', 'infoLabels':{'title':title,'artist':item['artist_name'],'album':item['title']}},
            'thumbnail': item['album_logo'],
            'is_playable': True,
            'context_menu': [
                (_L(30101), actions.update_view(plugin.url_for('album', albumid=item['album_id']))),
                (_L(30102), actions.background(plugin.url_for('download_file', url=item['location']))),
            ]
        })
    return result

@plugin.route('/similar/artist/<artistid>')
def similar_artists(artistid):
    url = root_url+'/app/android/artist-similar?id='+artistid

    req = urllib2.Request(url, None, {'User-Agent':agent_str})
    content = urllib2.urlopen(req, timeout=5).read()
    data = simplejson.loads(content)
    result = []
    for item in data['artists']:
        name = unescape_name(item['name'])
        artistid = item['artist_id']
        result.append({
            'label': name,
            'path': plugin.url_for('artist_top', artistid=artistid),
            'thumbnail': item['logo'],
            'context_menu': [
                (_L(30103), actions.update_view(plugin.url_for('topsongs', artistid=artistid))),
                (_L(30104), actions.update_view(plugin.url_for('similar_artists', artistid=artistid))),
            ]
        })
    return plugin.finish(result, view_mode='thumbnail')

@plugin.route('/song/<songid>')
def song(songid):
    url = root_url+'/app/iphone/song/id/'+songid

    req = urllib2.Request(url, None, {'User-Agent':agent_str})
    content = urllib2.urlopen(req, timeout=5).read()
    data = simplejson.loads(content)
    mp3_url = root_url+data['location']

    plugin.set_resolved_url(mp3_url)

@plugin.route('/download/file')
def download_file(url):
    plugin.log.debug(url)
    import xbmcvfs
    wdir = plugin.get_setting('download_dir', unicode)
    if not xbmcvfs.exists(wdir):
        return plugin.finish(None, succeeded=False)
    wpath = os.path.join(wdir, url.rsplit('/',1)[-1])

    req = urllib2.Request(url)
    r = urllib2.urlopen(req)
    f = xbmcvfs.File(wpath, 'w')
    while True:
        buf = r.read(512*1024)
        if len(buf) == 0:
            break
        f.write(buf)
    r.close()
    f.close()
    plugin.notify(_L(30105) % wpath.encode('utf-8'))
    return plugin.finish(None, succeeded=True)

if __name__ == "__main__":
    plugin.run()

# vim:sw=4:sts=4:et
