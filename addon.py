# -*- coding: utf-8 -*-
# http://www.xiami.com/

#   /chart/data?c=101&type=[0-4]&page=1&limit=25
#      type/[0-4] - [all|huayu|oumei|ri|han]

#   /[artist|album]/index/c/[1-2]/type/[0-3]
#      c/1 - Popular
#      c/2 - Recommended

#   /genre/songs/sid/<sid>
#   /genre/albums/sid/<sid>
#   /genre/artists/sid/<sid>
#     or sid => gid

from xbmcswift2 import Plugin, actions

plugin = Plugin()
_L = plugin.get_string

import urllib, urllib2
from BeautifulSoup import BeautifulSoup
import json
import re
import os
import collections

ROOT_URL = "http://www.xiami.com"
HTTP_HEADERS = {
    "User-Agent" : "Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19"
}
xiamiToken = '9c2fdceeb13ac5521b3f0f72a20f6d2a'

tPrevPage = u"[B]<<[/B]%s" % _L(30000)
tNextPage = u"%s[B]>>[/B]" % _L(30001)

def unescape_name(s):
    return s.replace('&amp;','&').replace('&#039;',"'")

@plugin.route('/')
def main_menu():
    items = [
        {'label':_L(30018), 'path':plugin.url_for('bang_albums_menu', type='new')},
        {'label':_L(30019), 'path':plugin.url_for('bang_albums_menu', type='hot')},
        {'label':_L(30025), 'path':plugin.url_for('chart_menu')},
        {'label':_L(30032), 'path':plugin.url_for('genre_menu')},
        {'label':_L(30031), 'path':plugin.url_for('search_menu')},
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
    url = ROOT_URL+'/web/bang-albums?type=%s&style=%s' % (type, style)
    plugin.log.debug(url)
    req = urllib2.Request(url, headers=HTTP_HEADERS)
    content = urllib2.urlopen(req, timeout=5).read()
    data = json.loads(content)

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
    img_base = 'http://img.xiami.net/res/img/default/charts200/'
    items = [
        {'label':_L(30020), 'path':plugin.url_for('chart', type='all')},
        {'label':_L(30021), 'path':plugin.url_for('chart', type='huayu'), 'thumbnail':img_base+'hua-hot.png'},
        {'label':_L(30022), 'path':plugin.url_for('chart', type='oumei'), 'thumbnail':img_base+'oumei-hot.png'},
        {'label':_L(30026), 'path':plugin.url_for('chart', type='rihan'), 'thumbnail':img_base+'rihan-hot.png'},
        #
        {'label':_L(30027), 'path':plugin.url_for('chart', type='billboard'), 'thumbnail':img_base+'bill.png'},
        {'label':_L(30028), 'path':plugin.url_for('chart', type='uk'), 'thumbnail':img_base+'eng-uk.png'},
        {'label':_L(30029), 'path':plugin.url_for('chart', type='oricon'), 'thumbnail':img_base+'ori.png'},
        {'label':_L(30030), 'path':plugin.url_for('chart', type='mnet'), 'thumbnail':img_base+'ment.png'},
        {'label':_L(30036), 'path':plugin.url_for('chart', type='hito'), 'thumbnail':img_base+'hito.png'},
        {'label':_L(30037), 'path':plugin.url_for('chart', type='jinge'), 'thumbnail':img_base+'tvb.png'},
    ]
    return plugin.finish(items, view_mode='thumbnail')

@plugin.route('/chart/<type>')
def chart(type):
    url = ROOT_URL+'/web/get-songs?type=%s&rtype=%s&id=0&_xiamitoken=%s' % (type, 'bang', xiamiToken)
    plugin.log.debug(url)
    headers = HTTP_HEADERS
    headers['Referer'] = 'http://www.xiami.com/web/spark'
    headers['Cookie'] = '_xiamitoken=%s' % xiamiToken
    req = urllib2.Request(url, headers=headers)
    content = urllib2.urlopen(req, timeout=5).read()
    data = json.loads(content)

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
    #plugin.add_to_playlist(result, playlist='music')
    return result

@plugin.route('/genre_top')
def genre_menu():
    items = []
    for gtit, gdat in get_genres().items():
        items.append({'label':gtit, 'path':plugin.url_for('genre_list', gid=gdat['id'])})
    return items

@plugin.route('/genre_list/<gid>')
def genre_list(gid):
    for gtit, gdat in get_genres().items():
        if gdat['id'] == int(gid):
            items = []
            for stit, sdat in gdat['sub'].items():
                items.append({'label':stit, 'path':plugin.url_for('genre_view_menu', sid=sdat['id'])})
            return items
    return None

@plugin.route('/genre_view_top/<sid>')
def genre_view_menu(sid):
    items = [
        {'label':_L(30033), 'path':plugin.url_for('genre_view', domain='songs', sid=sid, page=1)},
        {'label':_L(30034), 'path':plugin.url_for('genre_view', domain='albums', sid=sid, page=1)},
        {'label':_L(30035), 'path':plugin.url_for('genre_view', domain='artists', sid=sid, page=1)},
    ]
    return items

@plugin.route('/genre/<domain>/<sid>')
def genre_view(domain, sid, page='1'):
    url = ROOT_URL+"/genre/%s/sid/%s/page/%s" % (domain, sid, page)

    req = urllib2.Request(url, headers=HTTP_HEADERS)
    content = urllib2.urlopen(req, timeout=5).read()
    html = BeautifulSoup(content)
    result = []
    for item in html.findAll('div', {'class':'info'}):
        thumb = item.parent.find('img')['src']
        a_tags = item.findAll('a')
        c_id = a_tags[0]['href'].split('/')[-1]
        if domain == 'songs':
            result.append({
                'label': unescape_name(a_tags[0].text),     # song
                'label2': unescape_name(a_tags[1].text),    # artist
                'path': plugin.url_for('song', songid=c_id),
                'thumbnail': thumb,
                'is_playable': True
            })
        elif domain == 'albums':
            result.append({
                'label': unescape_name(a_tags[0].text),     # album
                'label2': unescape_name(a_tags[1].text),    # artist
                'path': plugin.url_for('album', albumid=c_id),
                'thumbnail': thumb,
            })
        elif domain == 'artists':
            result.append({
                'label': unescape_name(a_tags[0].text),
                'path': plugin.url_for('artist_top', artistid=c_id),
                'thumbnail': thumb,
            })
    #if domain == 'songs':
    #    plugin.add_to_playlist(result, playlist='music')
    ### navigation
    nav = html.find('div', {'id':'pagination'})
    if nav.find('a', {'class':'p_redirect'}):
        result.append({
            'label': tPrevPage,
            'path': plugin.url_for('genre_view', domain=domain, sid=sid, page=int(page)-1)
        })
    if nav.find('a', {'class':'p_redirect_l'}):
        result.append({
            'label': tNextPage,
            'path': plugin.url_for('genre_view', domain=domain, sid=sid, page=int(page)+1)
        })
    return plugin.finish(result, view_mode='thumbnail')

@plugin.route('/search_top')
def search_menu():
    items = [
        {'label':_L(30010), 'path':plugin.url_for('search', domain='artist')},
        {'label':_L(30011), 'path':plugin.url_for('search', domain='album')},
    ]
    return items

@plugin.route('/search/<domain>')
def search(domain):
    keywd = plugin.keyboard(heading='Keyword')
    if not keywd:
    	return None

    url = ROOT_URL+"/search/%s?key=%s" % (domain, urllib.quote_plus(keywd))

    req = urllib2.Request(url, headers=HTTP_HEADERS)
    content = urllib2.urlopen(req, timeout=5).read()
    html = BeautifulSoup(content)
    result = []
    for item in html.findAll('div', {'class':re.compile('_item100_block')}):
        title = ''.join(item.find('p', {'class':'name'}).a.findAll(text=True))
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
            album_node = item.find('a', {'class':'CDcover100'})
            albumid = album_node['href'].split('/')[-1]
            artist_node = item.find('a', {'class':'singer'})
            artistid = artist_node['href'].split('/')[-1]
            artist_name = artist_node.string
            result.append({
                'label': title,
                'label2': artist_name,
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
    if not id:
        return None
    return plugin.redirect( plugin.url_for('artist_top', artistid=id) )

@plugin.route('/jump/album')
def album_input():
    id = plugin.keyboard(heading='Album ID')
    if not id:
        return None
    return plugin.redirect( plugin.url_for('album', albumid=id) )

@plugin.route('/jump/collect')
def collect_input():
    id = plugin.keyboard(heading='Collect ID')
    if not id:
        return None
    return plugin.redirect( plugin.url_for('collect', collectid=id) )

@plugin.route('/artist/<artistid>')
def artist_top(artistid):
    # artist info
    url = ROOT_URL+'/app/android/artist?id='+artistid
    req = urllib2.Request(url, headers=HTTP_HEADERS)
    content = urllib2.urlopen(req, timeout=5).read()
    data = json.loads(content)
    albums_count = data['artist']['albums_count']

    plugin.redirect( plugin.url_for('artist', artistid=artistid, albumscnt=albums_count, page='0') )

@plugin.route('/artist/<artistid>/<albumscnt>')
def artist(artistid, albumscnt, page='0'):
    albums_count = int(albumscnt)
    pageN = 1 if page == '0' else int(page)

    # discography
    url = ROOT_URL+'/app/android/artist-albums?id=%s&page=%d' % (artistid, pageN)
    plugin.log.debug(url)

    req = urllib2.Request(url, headers=HTTP_HEADERS)
    content = urllib2.urlopen(req, timeout=5).read()
    data = json.loads(content)
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
    url = ROOT_URL+'/app/android/album?id='+albumid

    req = urllib2.Request(url, headers=HTTP_HEADERS)
    content = urllib2.urlopen(req, timeout=5).read()
    data = json.loads(content)
    result = []
    for item in data['album']['songs']:
        title = unescape_name(item['name'])
        lyric = None
        if item['lyric'] and item['lyric'].startswith('http'):
            req = urllib2.Request(url, headers=HTTP_HEADERS)
            lyric = urllib2.urlopen(req, timeout=5).read()
        result.append({
            'label': title,
            'path': item['location'],
            'info': {'type':'music', 'infoLabels':[('tracknumber',int(item['track'])),('title',title),('lyrics',lyric)]},
            'thumbnail': item['album_logo'],
            'is_playable': True,
            'context_menu': [
                (_L(30100), actions.update_view(plugin.url_for('artist_top', artistid=item['artist_id']))),
                (_L(30102), actions.background(plugin.url_for('download_file', url=item['location']))),
            ]
        })
    #plugin.add_to_playlist(result, playlist='music')
    return result

@plugin.route('/collect/<collectid>')
def collect(collectid):
    url = ROOT_URL+'/app/android/collect?id=%s' % collectid
    req = urllib2.Request(url, headers=HTTP_HEADERS)
    content = urllib2.urlopen(req, timeout=5).read()
    data = json.loads(content)
    result = []
    for item in data['collect']['songs']:
        title = unescape_name(item['name'])
        lyric = None
        if item['lyric'] and item['lyric'].startswith('http'):
            req = urllib2.Request(url, headers=HTTP_HEADERS)
            lyric = urllib2.urlopen(req, timeout=5).read()
        result.append({
            'label': title,
            'label2': item['artist_name'],
            'path': item['location'],
            'info': {'type':'music', 'infoLabels':[('title',title),('album',item['title']),('artist',item['artist_name']),('lyrics',lyric)]},
            'thumbnail': item['album_logo'],
            'is_playable': True,
            'context_menu': [
                (_L(30100), actions.update_view(plugin.url_for('artist_top', artistid=item['artist_id']))),
                (_L(30101), actions.update_view(plugin.url_for('album', albumid=item['album_id']))),
                (_L(30102), actions.background(plugin.url_for('download_file', url=item['location']))),
            ]
        })
    #plugin.add_to_playlist(result, playlist='music')
    return plugin.finish(result, view_mode='thumbnail')

@plugin.route('/topsongs/<artistid>')
def topsongs(artistid):
    url = ROOT_URL+'/app/android/artist-topsongs?id='+artistid

    req = urllib2.Request(url, headers=HTTP_HEADERS)
    content = urllib2.urlopen(req, timeout=5).read()
    data = json.loads(content)
    result = []
    for item in data['songs']:
        title = unescape_name(item['name'])
        lyric = None
        if item['lyric'] and item['lyric'].startswith('http'):
            req = urllib2.Request(url, headers=HTTP_HEADERS)
            lyric = urllib2.urlopen(req, timeout=5).read()
        result.append({
            'label': title,
            'path': item['location'],
            'info': {'type':'music', 'infoLabels':[('title',title),('artist',item['artist_name']),('album',item['title']),('lyrics',lyric)]},
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
    url = ROOT_URL+'/app/android/artist-similar?id='+artistid

    req = urllib2.Request(url, headers=HTTP_HEADERS)
    content = urllib2.urlopen(req, timeout=5).read()
    data = json.loads(content)
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
    url = ROOT_URL+'/app/android/song/id/'+songid

    req = urllib2.Request(url, headers=HTTP_HEADERS)
    content = urllib2.urlopen(req, timeout=5).read()
    data = json.loads(content)
    mp3_url = data['song_location']

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

def get_genres():
    plugin_path = plugin.addon.getAddonInfo('path')
    gtbl_path = os.path.join(plugin_path, 'resources', 'genre.json')
    f = open(gtbl_path)
    return json.load(f, object_pairs_hook=collections.OrderedDict)

if __name__ == "__main__":
    plugin.run()

# vim:sw=4:sts=4:et
