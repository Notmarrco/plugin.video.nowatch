import xbmcplugin
import xbmcgui
import xbmc
import xbmcaddon

import urllib
import urllib2
import re
import os

from BeautifulSoup import SoupStrainer
from BeautifulSoup import BeautifulSoup


__plugin__ = 'nowatch.net'
__author__ = 'notmarrco'
__url__ = 'https://github.com/notmarrco/plugin.video.nowatch'
__date__ = '17-09-2012'
__version__ = '0.4'
__settings__ = xbmcaddon.Addon(id='plugin.video.nowatch')
# Path to the addon
pathAddon = __settings__.getAddonInfo('path')

#------------------------------------------------------------------------------
# Fonctions :

# Pour se simplifier la vie, une fonction qui recupere le contenu d'une url
def open_url(url):
    req = urllib2.Request(url)
    content = urllib2.urlopen(req)
    data = content.read()
    content.close()
#    return unicode( data, 'utf-8')
    return data

# On construit le menu principal en 2 etapes :
#
# 1. Recuperation des categories (nowatch.tv, .fm, etc.)
def get_categories(url):
    html = open_url(url)
    res = re.findall("""<li id="menu-item-\d+" class="menu-item menu-item-type-taxonomy menu-item-object-category ss-nav-menu-item-depth-1 ss-nav-menu-with-img"><a href="http://www.nowatch.net/category/nowatch-net/([^"]+)/">.*?<img .*? src="([^"]+)".*?<span class="wpmega-link-title">([^"]+)</span></a>\s+<ul class="sub-menu sub-menu-2">""",html)
  
    cats_list = {}
    for url, img, name in res:
        cats_list[name] = {'name' : name, 'url' : url, 'img' : img}
    return cats_list

# 2. Creation d'un dossier xbmc pour chaque categorie
def build_categories_menu(url):
    cats_list = get_categories(url)
    nb = len (cats_list.keys())
    for name, cat in cats_list.iteritems():
        addDir(name,cat['url'],1,cat['img'], nb)    
 
   
# Creation du sous menu, avec la liste des emissions, en 2 etapes egalement :
#
# 1. Recuperation des emissions   
def get_shows(ss_cat_url, url):
    html = open_url(url)
	
    res = re.findall("""<li id="menu-item-\d+" class="menu-item menu-item-type-taxonomy menu-item-object-category ss-nav-menu-item-depth-2"><a href="http://www.nowatch.net/category/nowatch-net/""" + ss_cat_url + """/([^"]+)/"><span class="wpmega-link-title">([^"]+)</span></a></li>""",html)
  
    ss_cats_list = {}
    for url, name in res:
        show_url = "http://www.nowatch.net/category/nowatch-net/" + ss_cat_url + "/" + url
        ss_cats_list[name] = {'url' : show_url}
    return ss_cats_list

# 2. Construction du sous menu des emissions de nowatch, en fonction de la categorie (tv,fm...) donnee
def build_shows_menu(name_cat, url, url_source):
    shows_list = get_shows(url, url_source)

    nb = len(shows_list.keys()) #nbr d'emissions pour la fenetre de chargement

    for name, ss_cat in shows_list.iteritems():
        # on utilise les logos des emissions stockees en local 
        # ou alors on les telecharge lors de la premiere utilisation
        res = os.path.join(pathAddon, 'resources/logos/'+clean(name) + '.jpg')
        if ( os.path.exists(res) ):
            img = [res]
        else:
            page = open_url( ss_cat['url'])
            img = re.findall("""<div class="aproposimg">.*?<img.*? src="([^"]+)" """,page) 
            try:
                img[0]
                urllib.urlretrieve(img[0], res)
                img = [res]
            except :
                img = ['default_todo']
        addDir(clean(name),ss_cat['url'],2,img[0], nb)


# Fonction qui construit le menu qui contient les episodes d'un show donne
def build_episodes_menu(name, url):
    # On scanne la page pour trouver le lien rss
    page = open_url(url)
    # On en profite pour recuperer l'image de l'episode (TODO : pour l'instant c'est celle du show global)
    logo_show = re.findall("""<div class="aproposimg">.*?<img.*? src="([^"]+)" """,page)
    try:
        logo_show[0]
    except :
        logo_show = ['default_todo']
    beautifulSoup = BeautifulSoup(page)
    # TODO : on devrait pouvoir se passer de beautifulSoup ...
    quality = __settings__.getSetting('quality')
    feeds = beautifulSoup.findAll("div", {'class' : 'feed'+quality.lower() } )
    try :
        feeds[0]
        url = feeds[0].a['href']
    except :
        feeds = beautifulSoup.findAll("div", {'class' : 'apropos' } )
        try :
            feeds[1]
            url = feeds[1].p.a['href']
        except :
            dia = xbmcgui.Dialog()
            ok = dia.ok(__plugin__,str("Erreur, pas de flux rss detecte"))
            return 0
            
    #TEMP DEBUG
    #dia = xbmcgui.Dialog()
    #ok = dia.ok(__plugin__,str(url))
    ## FIN TEMP

    rss = open_url(url)

#    try:
#        beautifulSoup = BeautifulSoup(rss)
#        itemRSS = beautifulSoup.findAll("item")
#        for item in itemRSS:
#            urltest = item.enclosure['url']
#            title = item.title.string
#            addLink(clean(title),urltest,logo_show[0])
#    except:
    try :
        test = re.findall("""<item>(.*?)</item>""", rss, re.DOTALL)
        for t in test:
            title = re.findall("""<title>(.*?)</title>""", t, re.DOTALL)[0]
            urltest = re.findall("""<media:content url="([^"]+)".*?/>""", t, re.DOTALL)
            try :
                urltest = urltest[0]
            except :
                urltest = re.findall("""<enclosure url="([^"]+)".*?/>""", t, re.DOTALL)[0]
            addLink(clean(title),urltest,logo_show[0])
    except :
        print "erreur, pas de video"

def play_video(url, name):
    # Lecture en streaming :
    image = xbmc.getInfoImage('') #ListItem.Thumb' )
    listitem = xbmcgui.ListItem(label = name , iconImage = 'DefaultVideo.png', thumbnailImage = image)
    listitem.setInfo( type = "Video", infoLabels={ "Title": name } ) #, "Director": __plugin__, "Studio": __plugin__, "Genre": 'podcast', "Plot": 'description', "Episode": 'episode'  } )
    xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(str(url), listitem)
    
    ##########TODO DEBUG #########
    #dia = xbmcgui.Dialog()
    #ok = dia.ok(__plugin__,str(url))

def clean(name):
	remove = [('&amp;','&'), ('&quot;','"'), ('&#039;','\''), ('&#038;','&'), ('&rsquo;','\''), ('\r\n',''), ('&apos;','\''), ('&#150;','-'), ('%3A',':'), ('%2F','/'), ('<link>',''), ('</link>','')]
	for trash, crap in remove:
		name = name.replace(trash,crap)
	return name
	
#------------------------------------------------------------------------------
# Elements classiques d'un plugin XBMC

def addLink(name,url,iconimage):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode=3&name="+urllib.quote_plus(name)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
    return ok

def addDir(name,url,mode,iconimage,nb):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True, totalItems=nb)
    return ok

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

params=get_params()
url=None
name=None
mode=None
try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass
print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

url_source = "http://www.nowatch.net/"

if mode==None or url==None or len(url)<1:
    build_categories_menu(url_source)
elif mode==1: 
    build_shows_menu(name, url, url_source)
elif mode== 2:
    build_episodes_menu(name, url)    
elif mode == 3:
    play_video(url, name)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
