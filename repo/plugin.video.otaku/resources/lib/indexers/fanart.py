import requests

baseUrl = "https://webservice.fanart.tv/v3"
lang = ['en', 'ja', '']
headers = {'Api-Key': "dfe6380e34f49f9b2b9518184922b49c"}


def getArt(meta_ids, mtype):
    art = {}
    if mid := meta_ids.get('themoviedb_id') if mtype == 'movies' else meta_ids.get('thetvdb_id'):
        r = requests.get(f'{baseUrl}/{mtype}/{mid}', headers=headers)
        res = r.json() if r.ok else {}
        if res:
            if mtype == 'movies':
                if res.get('moviebackground'):
                    items = []
                    for item in res['moviebackground']:
                        if item.get('lang') in lang:
                            items.append(item.get('url'))
                    art['fanart'] = items
                if res.get('moviethumb'):
                    items = []
                    for item in res['moviethumb']:
                        if item.get('lang') in lang:
                            items.append(item.get('url'))
                    art['thumb'] = items
            else:
                if res.get('showbackground'):
                    items = []
                    for item in res['showbackground']:
                        if item.get('lang') in lang:
                            items.append(item.get('url'))
                    art['fanart'] = items
                if res.get('tvthumb'):
                    items = []
                    for item in res['tvthumb']:
                        if item.get('lang') in lang:
                            items.append(item.get('url'))
                    art['thumb'] = items

            if res.get('clearart'):
                items = []
                for item in res['clearart']:
                    if item.get('lang') in lang:
                        items.append(item.get('url'))
                art['clearart'] = items
            elif res.get('hdclearart'):
                items = []
                for item in res['hdclearart']:
                    if item.get('lang') in lang:
                        items.append(item.get('url'))
                art['clearart'] = items
            elif res.get('hdmovieclearart'):
                items = []
                for item in res['hdmovieclearart']:
                    if item.get('lang') in lang:
                        items.append(item.get('url'))
                art['clearart'] = items

            if res.get('clearlogo'):
                items = []
                for item in res['clearlogo']:
                    if item.get('lang') in lang:
                        items.append(item.get('url'))
                art['clearlogo'] = items
            elif res.get('hdtvlogo'):
                items = []
                for item in res['hdtvlogo']:
                    if item.get('lang') in lang:
                        items.append(item.get('url'))
                art['clearlogo'] = items
            elif res.get('hdmovielogo'):
                items = []
                for item in res['hdmovielogo']:
                    if item.get('lang') in lang:
                        items.append(item.get('url'))
                art['clearlogo'] = items
    return art
