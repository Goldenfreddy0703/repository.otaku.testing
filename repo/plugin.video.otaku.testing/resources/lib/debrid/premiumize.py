import xbmc
import requests

from resources.lib.ui import source_utils, control


class Premiumize:
    def __init__(self):
        # self.client_id = "855400527"      # Swag
        self.client_id = '807831898'        # Otaku
        self.token = control.getSetting('premiumize.token')
        self.base_url = 'https://www.premiumize.me/api'
        self.OauthTimeStep = 0
        self.OauthTimeout = 0
        self.OauthTotalTimeout = 0

    def headers(self):
        return {'Authorization': f"Bearer {self.token}"}

    def auth(self):
        data = {'client_id': self.client_id, 'response_type': 'device_code'}
        r = requests.post('https://www.premiumize.me/token', data=data)
        resp = r.json()
        self.OauthTotalTimeout = self.OauthTimeout = resp['expires_in']
        self.OauthTimeStep = int(resp['interval'])
        copied = control.copy2clip(resp['user_code'])
        display_dialog = (f"{control.lang(30020).format(control.colorstr(resp['verification_uri']))}[CR]"
                          f"{control.lang(30021).format(control.colorstr(resp['user_code']))}")
        if copied:
            display_dialog = f"{display_dialog}[CR]{control.lang(30022)}"
        control.progressDialog.create(f'{control.ADDON_NAME}: Premiumize Auth', display_dialog)
        control.progressDialog.update(100)

        auth_done = False
        while not auth_done and self.OauthTimeout > 0:
            self.OauthTimeout -= self.OauthTimeStep
            xbmc.sleep(self.OauthTimeStep * 1000)
            auth_done = self.auth_loop(resp['device_code'])
        control.progressDialog.close()

        if auth_done:
            self.status()

    def status(self):
        r = requests.get(f'{self.base_url}/account/info', headers=self.headers())
        user_information = r.json()
        premium = user_information['premium_until'] > 0
        control.setSetting('premiumize.username', user_information['customer_id'])
        control.ok_dialog(control.ADDON_NAME, f'Premiumize {control.lang(30023)}')
        if not premium:
            control.setSetting('premiumize.auth.status', 'Expired')
            control.ok_dialog(f'{control.ADDON_NAME}: Premiumize', control.lang(30024))
        else:
            control.setSetting('premiumize.auth.status', 'Premium')

    def auth_loop(self, device_code):
        if control.progressDialog.iscanceled():
            self.OauthTimeout = 0
            return False
        control.progressDialog.update(int(self.OauthTimeout / self.OauthTotalTimeout * 100))
        data = {'client_id': self.client_id, 'code': device_code, 'grant_type': 'device_code'}
        r = requests.post('https://www.premiumize.me/token', data=data)
        token = r.json()
        if r.ok:
            self.token = token['access_token']
            control.setSetting('premiumize.token', self.token)
            return True
        else:
            if token.get('error') == 'access_denied':
                self.OauthTimeout = 0
            if token.get('error') == 'slow_down':
                xbmc.sleep(1000)
        return False
    
    def search_folder(self, query):
        params = {'q': query}
        r = requests.get(f'{self.base_url}/folder/search', headers=self.headers(), params=params)
        return r.json()['content']

    def list_folder(self, folderid):
        params = {'id': folderid} if folderid else None
        r = requests.get(f"{self.base_url}/folder/list", headers=self.headers(), params=params)
        return r.json()['content']

    def hash_check(self, hashlist):
        params = {'items[]': hashlist}
        r = requests.get(f'{self.base_url}/cache/check', headers=self.headers(), params=params)
        return r.json()

    def direct_download(self, src):
        postData = {'src': src}
        r = requests.post(f'{self.base_url}/transfer/directdl', headers=self.headers(), data=postData)
        return r.json()

    def addMagnet(self, src):
        postData = {'src': src}
        r = requests.post(f'{self.base_url}/transfer/create', headers=self.headers(), data=postData)
        return r.json()

    def transfer_list(self):
        r = requests.get(f'{self.base_url}/transfer/list', headers=self.headers())
        return r.json()['transfers']

    def delete_torrent(self, torrent_id):
        params = {'id': torrent_id}
        r = requests.post(f'{self.base_url}/transfer/delete', headers=self.headers(), params=params)
        return r.json()

    def resolve_hoster(self, source):
        directLink = self.direct_download(source)
        return directLink['location'] if directLink['status'] == 'success' else None

    def resolve_single_magnet(self, hash_, magnet, episode, pack_select):
        folder_details = self.direct_download(magnet)['content']
        folder_details = sorted(folder_details, key=lambda i: int(i['size']), reverse=True)
        folder_details = [i for i in folder_details if source_utils.is_file_ext_valid(i['link'])]
        filter_list = [i for i in folder_details]

        if pack_select:
            identified_file = source_utils.get_best_match('path', folder_details, episode, pack_select)
            stream_link = identified_file.get('link')
            return stream_link

        elif len(filter_list) == 1:
            stream_link = filter_list[0]['link']
            return stream_link

        elif len(filter_list) >= 1:
            identified_file = source_utils.get_best_match('path', folder_details, episode)
            stream_link = identified_file.get('link')
            return stream_link

        filter_list = [tfile for tfile in folder_details if 'sample' not in tfile['path'].lower()]

        if len(filter_list) == 1:
            stream_link = filter_list[0]['link']
            return stream_link

    def resolve_cloud(self, source, pack_select):
        link = None
        if source['torrent_type'] == 'file':
            link = source['hash']
        elif source['torrent_type'] == 'folder':
            torrent_folder = self.list_folder(source['id'])
            best_match = source_utils.get_best_match('name', torrent_folder, source['episode'], pack_select)
            if best_match and best_match.get('link'):
                link = best_match['link']
        return link

    def resolve_uncached_source(self, source, runinbackground):
        heading = f'{control.ADDON_NAME}: Cache Resolver'
        if not runinbackground:
            control.progressDialog.create(heading, "Caching Progress")
        stream_link = None
        torrent = self.addMagnet(source['magnet'])
        if runinbackground:
            control.notify(heading, "The souce is downloading to your cloud")
            return

        progress = 0
        status = 'running'
        while status != 'finished':
            if control.progressDialog.iscanceled() or control.wait_for_abort(5):
                break
            transfer_list = self.transfer_list()
            for i in transfer_list:
                if i['id'] == torrent['id']:
                    status = i['status']
                    try:
                        progress = float(i['progress'] * 100)
                    except TypeError:
                        control.log(i)
                    f_body = (f"Progress: {round(progress, 2)} %[CR]"
                              f"Status: {status}")
                    control.progressDialog.update(int(progress), f_body)
                    break
            else:
                control.log('Unable to find torrent', 'warning')
                break
        if status == 'finished':
            control.ok_dialog(heading, "This file has been added to your Cloud")
        else:
            self.delete_torrent(torrent['id'])
            # torrent_list = self.list_folder(torrent['id'])
            # if torrent_list['transcode_status'] == 'finished':
            #     stream_link = self.resolve_cloud(source, False)
        control.progressDialog.close()
        return stream_link
