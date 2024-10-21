import threading
import requests
import xbmc

from resources.lib.ui import control, source_utils


class AllDebrid:
    def __init__(self):
        self.apikey = control.getSetting('alldebrid.apikey')
        self.agent_identifier = 'Otaku'
        self.base_url = 'https://api.alldebrid.com/v4'
        self.cache_check_results = []

    def auth(self):
        params = {
            'agent': self.agent_identifier
        }
        resp = requests.get(f'{self.base_url}/pin/get', params=params).json()['data']
        expiry = pin_ttl = int(resp['expires_in'])
        auth_complete = False
        control.copy2clip(resp['pin'])
        control.progressDialog.create(
            control.ADDON_NAME + ': AllDebrid Auth',
            control.lang(30020).format(control.colorstr(resp['base_url'])) + '[CR]'
            + control.lang(30021).format(control.colorstr(resp['pin'])) + '[CR]'
            + control.lang(30022)
        )
        # Seems the All Debrid servers need some time do something with the pin before polling
        # Polling too early will cause an invalid pin error
        xbmc.sleep(5000)
        control.progressDialog.update(100)
        while not auth_complete and not expiry <= 0 and not control.progressDialog.iscanceled():
            xbmc.sleep(1000)
            auth_complete, expiry = self.poll_auth(check=resp['check'], pin=resp['pin'])
            progress_percent = 100 - int((float(pin_ttl - expiry) / pin_ttl) * 100)
            control.progressDialog.update(progress_percent)
        control.progressDialog.close()
        params = {
            'agent': self.agent_identifier,
            'apikey': self.apikey
        }
        r = requests.get(f'{self.base_url}/user', params=params)
        res = r.json().get('data', {})
        user_information = res.get('user')
        if user_information:
            control.setSetting('alldebrid.username', user_information['username'])
            control.setSetting('alldebrid.auth.status', 'Premium' if user_information['isPremium'] else 'expired')
            if auth_complete:
                control.ok_dialog(control.ADDON_NAME, f'AllDebrid {control.lang(30023)}')
        else:
            control.ok_dialog(control.ADDON_NAME, 'AllDebrid Failed to login')

    def poll_auth(self, **params):
        params['agent'] = self.agent_identifier
        r = requests.get(f'{self.base_url}/pin/check', params=params)
        resp = r.json()['data']
        if resp['activated']:
            control.setSetting('alldebrid.apikey', resp['apikey'])
            self.apikey = resp['apikey']
            return True, 0
        return False, int(resp['expires_in'])

    def check_hash(self, hashlist):
        self.cache_check_results = []
        hashlist = [hashlist[x: x + 10] for x in range(0, len(hashlist), 10)]
        threads = []
        for hash_ in hashlist:
            thread = threading.Thread(target=self._check_hash_thread, args=[hash_])
            threads.append(thread)
            thread.start()
        for i in threads:
            i.join()
        return self.cache_check_results

    def _check_hash_thread(self, hashes):
        params = {
            'agent': self.agent_identifier,
            'apikey': self.apikey,
            'magnets[]': hashes
        }
        r = requests.post(f'{self.base_url}/magnet/instant', params=params)

        response = r.json()['data']
        self.cache_check_results += response.get('magnets')

    def addMagnet(self, magnet_hash):
        params = {
            'agent': self.agent_identifier,
            'apikey': self.apikey,
            'magnets': magnet_hash
        }
        r = requests.get(f'{self.base_url}/magnet/upload', params=params)
        return r.json()['data']

    def resolve_hoster(self, url):
        params = {
            'agent': self.agent_identifier,
            'apikey': self.apikey,
            'link': url
        }
        r = requests.get(f'{self.base_url}/link/unlock', params=params)
        resolve = r.json()['data']
        return resolve['link']

    def magnet_status(self, magnet_id):
        params = {
            'agent': self.agent_identifier,
            'apikey': self.apikey,
            'id': magnet_id
        }
        r = requests.get(f'{self.base_url}/magnet/status', params=params)
        return r.json()['data']

    def list_torrents(self):
        params = {
            'agent': self.agent_identifier,
            'apikey': self.apikey
        }
        r = requests.get(f'{self.base_url}/user/links', params=params)
        return r.json()['data']

    def link_info(self, link):
        params = {
            'agent': self.agent_identifier,
            'apikey': self.apikey,
            'link[]': link
        }
        r = requests.get(f'{self.base_url}/link/infos', params=params)
        return r.json()['data']

    def resolve_single_magnet(self, hash_, magnet, episode='', pack_select=False):
        magnet_id = self.addMagnet(magnet)['magnets'][0]['id']
        folder_details = self.magnet_status(magnet_id)['magnets']['links']
        folder_details = [{'link': x['link'], 'path': x['filename']} for x in folder_details]

        if episode:
            selected_file = source_utils.get_best_match('path', folder_details, episode, pack_select)
            self.delete_magnet(magnet_id)
            if selected_file is not None:
                return self.resolve_hoster(selected_file['link'])

        selected_file = folder_details[0]['link']

        if selected_file is None:
            return

        self.delete_magnet(magnet_id)
        return self.resolve_hoster(selected_file)

    def delete_magnet(self, magnet_id):
        params = {
            'agent': self.agent_identifier,
            'apikey': self.apikey,
            'id': magnet_id
        }
        r = requests.get(f'{self.base_url}/magnet/delete', params=params)
        return r.ok

    @staticmethod
    def resolve_uncached_source(source, runinbackground):
        heading = f'{control.ADDON_NAME}: Cache Resolver'
        control.ok_dialog(heading, 'Cache Reolver Has not been added for Premiumize')
