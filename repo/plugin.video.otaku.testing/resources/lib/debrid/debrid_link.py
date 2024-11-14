import time
import requests
import threading
import xbmc

from resources.lib.ui import control, source_utils


class DebridLink:
    def __init__(self):
        self.ClientID = 'sdpBuYFQo6L53s3B4apluw'
        self.USER_AGENT = 'Otaku for Kodi'
        self.token = control.getSetting('dl.auth')
        self.refresh = control.getSetting('dl.refresh')
        self.headers = {
            'User-Agent': self.USER_AGENT,
            'Authorization': 'Bearer {0}'.format(self.token)
        }
        self.api_url = "https://debrid-link.fr/api/v2"
        self.cache_check_results = {}
        self.DeviceCode = None
        self.OauthTimeStep = None
        self.OauthTimeout = None

    def auth_loop(self):
        if control.progressDialog.iscanceled():
            control.progressDialog.close()
            return
        xbmc.sleep(self.OauthTimeStep)
        url = '{0}/oauth/token'.format(self.api_url[:-3])
        data = {
            'client_id': self.ClientID,
            'code': self.DeviceCode,
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
        }
        r = requests.post(url, data=data, headers={'User-Agent': self.USER_AGENT})
        if r.ok:
            response = r.json()
            control.progressDialog.close()
            self.token = response.get('access_token')
            self.refresh = response.get('refresh_token')
            control.setSetting('dl.auth', self.token)
            control.setSetting('dl.refresh', self.refresh)
            control.setInt('dl.expiry', int(time.time()) + int(response['expires_in']))
            self.headers['Authorization'] = 'Bearer {0}'.format(self.token)
        return True

    def auth(self):
        url = '{0}/oauth/device/code'.format(self.api_url[:-3])
        data = {'client_id': self.ClientID,
                'scope': 'get.post.delete.seedbox get.account'}
        response = requests.post(url, data=data, headers={'User-Agent': self.USER_AGENT}).json()
        self.OauthTimeout = response.get('expires_in')
        self.OauthTimeStep = response.get('interval')
        self.DeviceCode = response.get('device_code')

        control.copy2clip(response.get('user_code'))
        control.progressDialog.create('Debrid-Link Auth')
        control.progressDialog.update(
            -1,
            control.lang(30020).format(control.colorstr(response.get('verification_url'))) + '[CR]'
            + control.lang(30021).format(control.colorstr(response.get('user_code'))) + '[CR]'
            + control.lang(30022)
        )
        auth_done = False
        while not auth_done:
            auth_done = self.auth_loop()

        premium = self.get_info()
        if not premium:
            control.ok_dialog(control.ADDON_NAME, control.lang(30024))

    def get_info(self):
        url = '{0}/account/infos'.format(self.api_url[:-3])
        response = requests.get(url, headers=self.headers).json()
        username = response['value'].get('pseudo')
        control.setSetting('dl.username', username)
        control.ok_dialog(control.ADDON_NAME, 'Debrid-Link ' + control.lang(30023))
        return response['value'].get('premiumLeft') > 3600

    def refreshToken(self):
        postData = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh,
            'client_id': self.ClientID
        }
        url = '{0}/oauth/token'.format(self.api_url[:-3])
        response = requests.post(url, data=postData, headers={'User-Agent': self.USER_AGENT}).json()
        if 'access_token' in response:
            self.token = response.get('access_token')
            control.setSetting('dl.auth', self.token)
            control.setInt('dl.expiry', int(time.time()) + response.get('expires_in'))

    def check_hash(self, hashlist):
        if isinstance(hashlist, list):
            self.cache_check_results = {}
            hashlist = [hashlist[x: x + 100] for x in range(0, len(hashlist), 100)]
            threads = []
            for arg in hashlist:
                t = threading.Thread(target=self._check_hash_thread, args=[arg])
                threads.append(t)
                t.start()
            for i in threads:
                i.join()
            return self.cache_check_results
        else:
            url = "{0}/seedbox/cached?url={1}".format(self.api_url, hashlist)
            response = requests.get(url, headers=self.headers).json()
            return response.get('value')

    def _check_hash_thread(self, hashes):
        hashString = ','.join(hashes)
        url = "{0}/seedbox/cached?url={1}".format(self.api_url, hashString)
        response = requests.get(url, headers=self.headers)
        if response.ok:
            self.cache_check_results.update(response.json().get('value'))

    def addMagnet(self, magnet):
        postData = {
            'url': magnet,
            'async': 'true'
        }
        url = '{0}/seedbox/add'.format(self.api_url)
        response = requests.post(url, data=postData, headers=self.headers).json()
        return response.get('value')

    def resolve_single_magnet(self, hash_, magnet, episode='', pack_select=False):
        files = self.addMagnet(magnet)['files']
        folder_details = [{'link': x['downloadUrl'], 'path': x['name']} for x in files]
        if episode:
            selected_file = source_utils.get_best_match('path', folder_details, episode, pack_select)
            if selected_file is not None:
                return selected_file['link']

        sources = [(item.get('size'), item.get('downloadUrl'))for item in files if any(item.get('name').lower().endswith(x) for x in ['avi', 'mp4', 'mkv'])]

        selected_file = max(sources)[1]
        if selected_file is None:
            return

        return selected_file

    @staticmethod
    def resolve_uncached_source(source, runinbackground):
        heading = f'{control.ADDON_NAME}: Cache Resolver'
        control.ok_dialog(heading, 'Cache Reolver Has not been added for Premiumize')
