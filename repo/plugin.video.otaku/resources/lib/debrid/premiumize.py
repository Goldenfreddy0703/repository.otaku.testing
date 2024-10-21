import xbmc
import requests

from urllib import parse
from resources.lib.ui import source_utils, control


class Premiumize:
    def __init__(self):
        self.client_id = "855400527"
        self.headers = {
            'Authorization': 'Bearer {}'.format(control.getSetting('premiumize.token'))
        }

    def auth(self):
        data = {'client_id': self.client_id, 'response_type': 'device_code'}
        token = requests.post('https://www.premiumize.me/token', data=data)
        token = token.json()
        expiry = token['expires_in']
        token_ttl = token['expires_in']
        poll_again = True
        success = False
        control.copy2clip(token['user_code'])
        control.progressDialog.create(
            control.ADDON_NAME,
            control.lang(30020).format(control.colorstr(token['verification_uri'])) + '[CR]'
            + control.lang(30021).format(control.colorstr(token['user_code'])) + '[CR]'
            + control.lang(30022)
        )
        control.progressDialog.update(0)

        while poll_again and not token_ttl <= 0 and not control.progressDialog.iscanceled():
            poll_again, success = self.poll_token(token['device_code'])
            progress_percent = 100 - int((float((expiry - token_ttl) / expiry) * 100))
            control.progressDialog.update(progress_percent)
            xbmc.sleep(token['interval'])
            token_ttl -= int(token['interval'])
        control.progressDialog.close()

        if success:
            control.ok_dialog(control.ADDON_NAME, 'Premiumize ' + control.lang(30023))

    def poll_token(self, device_code):
        data = {'client_id': self.client_id, 'code': device_code, 'grant_type': 'device_code'}
        token = requests.post('https://www.premiumize.me/token', data=data)
        token = token.json()
        control.setSetting('premiumize.token', token['access_token'])
        self.headers['Authorization'] = 'Bearer {}'.format(token['access_token'])

        account_info = self.account_info()
        control.setSetting('premiumize.username', account_info['customer_id'])

        return False, True

    def get_url(self, url):
        if self.headers['Authorization'] == 'Bearer ':
            return None
        url = "https://www.premiumize.me/api{}".format(url)
        req = requests.get(url, timeout=10, headers=self.headers)
        return req.json()

    def post_url(self, url, data):
        if self.headers['Authorization'] == 'Bearer ':
            return None
        url = "https://www.premiumize.me/api{}".format(url)
        req = requests.post(url, headers=self.headers, data=data, timeout=10)
        return req.json()

    def account_info(self):
        url = "/account/info"
        response = self.get_url(url)
        return response

    def list_folder(self, folderid):
        url = "/folder/list"
        postData = {'id': folderid} if folderid else ''
        response = self.post_url(url, postData)
        return response['content']

    def hash_check(self, hashlist):
        url = '/cache/check'
        hashString = '&'.join(['items[]=' + x for x in hashlist])
        response = self.get_url('{0}?{1}'.format(url, parse.quote(hashString, '=&')))
        return response

    def direct_download(self, src):
        postData = {'src': src}
        url = '/transfer/directdl'
        return self.post_url(url, postData)

    def resolve_hoster(self, source):
        directLink = self.direct_download(source)
        return directLink['location'] if directLink['status'] == 'success' else None

    def resolve_single_magnet(self, hash_, magnet, episode='', pack_select=False):
        folder_details = self.direct_download(magnet)['content']
        folder_details = sorted(folder_details, key=lambda i: int(i['size']), reverse=True)
        folder_details = [i for i in folder_details if source_utils.is_file_ext_valid(i['link'])]
        filter_list = [i for i in folder_details]

        if pack_select:
            identified_file = source_utils.get_best_match('path', folder_details, episode, pack_select)
            stream_link = self._fetch_transcode_or_standard(identified_file)
            return stream_link

        elif len(filter_list) == 1:
            stream_link = self._fetch_transcode_or_standard(filter_list[0])
            return stream_link

        elif len(filter_list) >= 1:
            identified_file = source_utils.get_best_match('path', folder_details, episode, pack_select)
            stream_link = self._fetch_transcode_or_standard(identified_file)
            return stream_link

        filter_list = [tfile for tfile in folder_details if 'sample' not in tfile['path'].lower()]

        if len(filter_list) == 1:
            stream_link = self._fetch_transcode_or_standard(filter_list[0])
            return stream_link

    @staticmethod
    def _fetch_transcode_or_standard(file_object):
        return file_object['link']

    @staticmethod
    def resolve_uncached_source(source, runinbackground):
        heading = f'{control.ADDON_NAME}: Cache Resolver'
        control.ok_dialog(heading, 'Cache Reolver Has not been added for Premiumize')
