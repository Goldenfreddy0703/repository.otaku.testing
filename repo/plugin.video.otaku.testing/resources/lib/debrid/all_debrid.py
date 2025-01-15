import requests
import xbmc

from resources.lib.ui import control, source_utils


class AllDebrid:
    def __init__(self):
        self.token = control.getSetting('alldebrid.token')
        self.agent_identifier = 'Otaku'
        self.base_url = 'https://api.alldebrid.com/v4'
        self.cache_check_results = []
        self.OauthTimeStep = 1
        self.OauthTimeout = 0
        self.OauthTotalTimeout = 0

    def auth(self):
        params = {'agent': self.agent_identifier}
        resp = requests.get(f'{self.base_url}/pin/get', params=params).json()['data']
        self.OauthTotalTimeout = self.OauthTimeout = int(resp['expires_in'])
        copied = control.copy2clip(resp['pin'])
        display_dialog = (f"{control.lang(30020).format(control.colorstr(resp['base_url']))}[CR]"
                          f"{control.lang(30021).format(control.colorstr(resp['pin']))}")
        if copied:
            display_dialog = f"{display_dialog}[CR]{control.lang(30022)}"
        control.progressDialog.create(f'{control.ADDON_NAME}: Alldebrid Auth', display_dialog)
        control.progressDialog.update(100)
        
        # Seems the All Debrid servers need some time do something with the pin before polling
        # Polling too early will cause an invalid pin error

        xbmc.sleep(5000)

        auth_done = False
        while not auth_done and self.OauthTimeout > 0:
            self.OauthTimeout -= self.OauthTimeStep
            xbmc.sleep(self.OauthTimeStep * 1000)
            auth_done = self.auth_loop(check=resp['check'], pin=resp['pin'])
        control.progressDialog.close()
        if auth_done:
            self.status()

    def status(self):
        params = {
            'agent': self.agent_identifier,
            'apikey': self.token
        }
        r = requests.get(f'{self.base_url}/user', params=params)
        res = r.json()['data']
        user_information = res['user']
        premium = user_information['isPremium']
        control.setSetting('alldebrid.username', user_information['username'])
        control.ok_dialog(control.ADDON_NAME, f'Alldebrid {control.lang(30023)}')
        if not premium:
            control.setSetting('alldebrid.auth.status', 'Expired')
            control.ok_dialog(f'{control.ADDON_NAME}: AllDebrid', control.lang(30024))
        else:
            control.setSetting('alldebrid.auth.status', 'Premium')

    def auth_loop(self, **params):
        if control.progressDialog.iscanceled():
            self.OauthTimeout = 0
            return False
        control.progressDialog.update(int(self.OauthTimeout / self.OauthTotalTimeout * 100))
        params['agent'] = self.agent_identifier
        r = requests.get(f'{self.base_url}/pin/check', params=params)
        resp = r.json()['data']
        if resp['activated']:
            self.token = resp['apikey']
            control.setSetting('alldebrid.token', self.token)
            return True
        return False

    def addMagnet(self, magnet_hash):
        params = {
            'agent': self.agent_identifier,
            'apikey': self.token,
            'magnets': magnet_hash
        }
        r = requests.get(f'{self.base_url}/magnet/upload', params=params)
        return r.json()['data']

    def resolve_hoster(self, url):
        params = {
            'agent': self.agent_identifier,
            'apikey': self.token,
            'link': url
        }
        r = requests.get(f'{self.base_url}/link/unlock', params=params)
        resolve = r.json()['data']
        return resolve['link']

    def magnet_status(self, magnet_id):
        params = {
            'agent': self.agent_identifier,
            'apikey': self.token,
            'id': magnet_id
        }
        r = requests.get(f'{self.base_url}/magnet/status', params=params)
        return r.json()['data']

    def list_torrents(self):
        params = {
            'agent': self.agent_identifier,
            'apikey': self.token
        }
        r = requests.get(f'{self.base_url}/user/links', params=params)
        return r.json()['data']

    def link_info(self, link):
        params = {
            'agent': self.agent_identifier,
            'apikey': self.token,
            'link[]': link
        }
        r = requests.get(f'{self.base_url}/link/infos', params=params)
        return r.json()['data']

    def resolve_single_magnet(self, hash_, magnet, episode, pack_select):
        magnet_id = self.addMagnet(magnet)['magnets'][0]['id']
        folder_details = self.magnet_status(magnet_id)['magnets']['links']
        folder_details = [{'link': x['link'], 'path': x['filename']} for x in folder_details]

        if episode:
            selected_file = source_utils.get_best_match('path', folder_details, str(episode), pack_select)
            self.delete_magnet(magnet_id)
            if selected_file is not None:
                return self.resolve_hoster(selected_file['link'])

        selected_file = folder_details[0]['link']

        if selected_file is None:
            return

        self.delete_magnet(magnet_id)
        return self.resolve_hoster(selected_file)

    def resolve_cloud(self, source, pack_select):
        pass

    def delete_magnet(self, magnet_id):
        params = {
            'agent': self.agent_identifier,
            'apikey': self.token,
            'id': magnet_id
        }
        r = requests.get(f'{self.base_url}/magnet/delete', params=params)
        return r.ok
