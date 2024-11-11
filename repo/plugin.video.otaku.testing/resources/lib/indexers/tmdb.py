import requests

apiKey = "6974ec27debf5cce1218136e2a36f64b"
baseUrl = "https://api.themoviedb.org/3/"
thumbPath = "https://image.tmdb.org/t/p/w500"
backgroundPath = "https://image.tmdb.org/t/p/original"


def getArt(meta_ids, mtype):
    art = {}
    mid = meta_ids.get('themoviedb_id')
    if mid is None:
        tvdb = meta_ids.get('thetvdb_id')
        if tvdb:
            params = {
                'external_source': 'tvdb_id',
                "api_key": apiKey
            }
            r = requests.get(f'{baseUrl}find/{tvdb}', params=params)
            res = r.json() if r.ok else {}
            res = res.get('tv_results')
            if res:
                mid = res[0].get('id')

    if mid:
        params = {
            'include_image_language': 'en,ja,null'
        }
        r = requests.get(f'{baseUrl}{mtype[0:5]}/{mid}/images', params=params)
        res = r.json() if r.ok else {}

        if res:
            if res.get('backdrops'):
                items = []
                items2 = []
                for item in res['backdrops']:
                    if item.get('file_path'):
                        items.append(backgroundPath + item['file_path'])
                        items.append(thumbPath + item['file_path'])
                art['fanart'] = items
                art['thumb'] = items2

            if res.get('logos'):
                items = [backgroundPath + item["url"] for item in res['logos'] if item.get('url')]
                art['clearart'] = items
    return art
