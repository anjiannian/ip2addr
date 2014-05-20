#!/usr/bin/env python
# encoding: utf-8

import urllib2
import logging
import memcache
from flask import Flask, render_template, request

try:
    import simplejson as json
except ImportError:
    import json

app = Flask(__name__)

#TAOBAOAPI = 'http://ip.taobao.com/service/getIpInfo.php?ip='
IPAPI = 'http://ip-api.com/json/'
GMAPS =  "http://maps.googleapis.com/maps/api/staticmap?size=440x440&sensor=false&"

points = []
memc = memcache.Client([('127.0.0.1', 11211)])

def gmaps_img(points):
  markers = '&'.join('markers=%s,%s' % p for p in points)
  return GMAPS + markers

@app.route('/')
def get_hostip():
    hostip =  str(request.remote_addr)
    logging.info('hostip %s' % hostip)
    return render_page(hostip)

@app.route('/', methods = ['POST'])
def get_ip():
    remoteip = request.form['ipaddress']
    #flash(remoteip)
    return render_page(remoteip)

def render_page(ip):
    '''Get the ip information from ip-api and parse it,
        give the information and google map location'''

    ipapi = memc.get(str(ip))

    if not ipapi:
        try:
            ipapi_page = urllib2.urlopen(IPAPI + ip).read()
        except urllib2.HTTPError, e:
            logging.error('HTTPError: ' + str(e.code))
        except urllib2.URLError, e:
            logging.error('URLError: ' + str(e.code))
        except Exception:
            logging.error('Some error occured while trying to open API!' )

        logging.info('To json %s' % ipapi_page)
        ipapi = json.loads(ipapi_page)
        memc.set(str(ip),ipapi,1296000)

    error = ''
    if ipapi['status'] == 'success':
        lat = ipapi['lat']
        lon = ipapi['lon']
        if len(points) > 50:
            points.pop(1)
        points.append((lat, lon))
        img_url = gmaps_img(points)
        return render_template('mainpage.html', hostip = ip,
                        country = ipapi['country'],
                        region = ipapi['regionName'],
                        city = ipapi['city'],
                        ISP = ipapi['isp'],
                        Latitude = lat,
                        Longitude = lon,
                        img_url = img_url)
    else:
        error = 'Sorry. We have no clue about your IP'
        return render_template('mainpage.html', error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8101)
