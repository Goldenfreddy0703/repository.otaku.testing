import time
import requests
import threading
import xbmc

from resources.lib.ui import control, source_utils


class DebridLink:
    def __init__(self):
        self.ClientID = 'sdpBuYFQo6L53s3B4apluw'
        self.USER_AGENT = 'Otaku'
        self.token = control.getSetting('debridlink.token')
        self.refresh = control.getSetting('debridlink.refresh')
        self.api_url = "https://debrid-link.com/api/v2"
        self.cache_check_results = {}
        self.DeviceCode = ''
        self.OauthTimeStep = 0
        self.OauthTimeout = 0
        self.OauthTotalTimeout = 0

    def headers(self):
        return {'User-Agent': self.USER_AGENT, 'Authorization': f"Bearer {self.token}"}

    def auth_loop(self):
        if control.progressDialog.iscanceled():
            control.progressDialog.close()
            self.OauthTimeout = 0
            return False
        control.progressDialog.update(int(self.OauthTimeout / self.OauthTotalTimeout * 100))
        url = f"{self.api_url[:-3]}/oauth/token"
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
            control.setSetting('debridlink.token', self.token)
            control.setSetting('debridlink.refresh', self.refresh)
            control.setInt('debridlink.expiry', int(time.time()) + int(response['expires_in']))
        return r.ok

    def auth(self):
        url = '{0}/oauth/device/code'.format(self.api_url[:-3])
        data = {'client_id': self.ClientID, 'scope': 'get.post.delete.seedbox get.account'}
        resp = requests.post(url, data=data, headers={'User-Agent': self.USER_AGENT}).json()

        self.OauthTotalTimeout = self.OauthTimeout = resp['expires_in']
        self.OauthTimeStep = resp['interval']
        self.DeviceCode = resp['device_code']

        copied = control.copy2clip(resp.get('user_code'))
        display_dialog = (f"{control.lang(30020).format(control.colorstr(resp['verification_url']))}[CR]"
                          f"{control.lang(30021).format(control.colorstr(resp['user_code']))}")
        if copied:
            display_dialog = f"{display_dialog}[CR]{control.lang(30022)}"
        control.progressDialog.create(f'{control.ADDON_NAME}: Debrid-Link Auth', display_dialog)
        control.progressDialog.update(100)
        auth_done = False
        while not auth_done and self.OauthTimeout > 0:
            self.OauthTimeout -= self.OauthTimeStep
            xbmc.sleep(self.OauthTimeStep * 1000)
            auth_done = self.auth_loop()
        if auth_done:
            self.status()

    def status(self):
        url = f"{self.api_url[:-3]}/account/infos"
        response = requests.get(url, headers=self.headers()).json()
        username = response['value']['pseudo']
        premium = response['value']['premiumLeft'] > 0
        control.setSetting('debridlink.username', username)
        control.ok_dialog(control.ADDON_NAME, f'Debrid-Link {control.lang(30023)}')
        if not premium:
            control.setSetting('debridlink.auth.status', 'Expired')
            control.ok_dialog(f'{control.ADDON_NAME}: Debrid-Link', control.lang(30024))
        else:
            control.setSetting('debridlink.auth.status', 'Premium')

    def refreshToken(self):
        postData = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh,
            'client_id': self.ClientID
        }
        url = f"{self.api_url[:-3]}/oauth/token"
        response = requests.post(url, data=postData, headers={'User-Agent': self.USER_AGENT}).json()
        if response.get('access_token'):
            self.token = response['access_token']
            control.setSetting('debridlink.token', self.token)
            control.setInt('debridlink.expiry', int(time.time()) + response['expires_in'])

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
            url = f"{self.api_url}/seedbox/cached?url={hashlist}"
            response = requests.get(url, headers=self.headers()).json()
            return response.get('value')

    def _check_hash_thread(self, hashes):
        hashString = ','.join(hashes)
        url = "{0}/seedbox/cached?url={1}".format(self.api_url, hashString)
        response = requests.get(url, headers=self.headers())
        if response.ok:
            self.cache_check_results.update(response.json().get('value'))

    def addMagnet(self, magnet):
        postData = {
            'url': magnet,
            'async': 'true'
        }
        url = f"{self.api_url}/seedbox/add"
        response = requests.post(url, data=postData, headers=self.headers()).json()
        return response.get('value')

    def resolve_single_magnet(self, hash_, magnet, episode, pack_select):
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
    def resolve_cloud(source, pack_selct):
        pass
