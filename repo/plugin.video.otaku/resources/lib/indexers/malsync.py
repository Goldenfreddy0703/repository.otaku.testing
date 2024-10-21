import requests

baseUrl = 'https://api.malsync.moe'


def get_slugs(mal_id, site=''):
    slugs = []
    if site in ['Gogoanime', 'Zoro']:
        r = requests.get(f'{baseUrl}/mal/anime/{mal_id}')
        resp = r.json()['Sites'].get(site)
        if resp:
            for key in resp.keys():
                slugs.append(resp[key].get('url'))
    return slugs
