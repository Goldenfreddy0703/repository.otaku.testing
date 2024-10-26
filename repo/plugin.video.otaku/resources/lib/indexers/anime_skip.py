import requests

base_url = "https://api.anime-skip.com/graphql"

headers = {
    "X-Client-ID": "buT57NJMu4G65vxGJWdj4UXgnq65Agfi"
}


def get_episode_ids(anilist_id, episode):
    query = '''
    query($service: ExternalService!, $serviceId: String!) {
        findShowsByExternalId(service: $service, serviceId: $serviceId) {
            episodes {
                id
                number
            }
        }
    }
'''
    variables = {
        'service': 'ANILIST',
        'serviceId': anilist_id
    }

    r = requests.post(base_url, headers=headers, json={'query': query, 'variables': variables})
    res = r.json()['data']['findShowsByExternalId']
    id_list = []
    for resx in res:
        for x in resx['episodes']:
            if x['number'] and int(x['number']) == episode:
                id_list.append(x['id'])
    return id_list


def get_time_stamps(id_list):
    query = '''
        query($episodeId: ID!) {
            findTimestampsByEpisodeId(episodeId: $episodeId) {
                at
                type {
                    name

                }  
            }
        }
    '''

    variables = {}
    res = {}
    for x in range(len(id_list)):
        variables['episodeId'] = id_list[x]
        r = requests.post(base_url, headers=headers, json={'query': query, 'variables': variables})
        res = r.json()['data']['findTimestampsByEpisodeId']
        if res:
            break
    return res


def convert_time_stamps(time_stamp, intro, outro):
    if not time_stamp:
        return
    skip_times = {}
    for skip in time_stamp:
        if intro:
            if skip['type']['name'] in ['Intro', 'Branding', 'New Intro']:
                skip_times['intro'] = {'start': skip['at']}
            elif skip_times.get('intro') and not skip_times['intro'].get('end') and skip['type']['name'] == 'Canon':
                skip_times['intro']['end'] = skip['at']
        if outro:
            if skip['type']['name'] in ['Credits', 'Mixed Credits']:
                skip_times['outro'] = {'start': skip['at']}
            elif skip_times.get('outro') and skip['type']['name'] == 'Preview':
                skip_times['outro']['end'] = skip['at']
    return skip_times
