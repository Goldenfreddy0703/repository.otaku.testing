import os

from resources.lib.ui import control


def allocate_item(name, url, isfolder, isplayable, image='', info=None, fanart=None, poster=None, cast=None, landscape=None, banner=None, clearart=None, clearlogo=None):
    if image and '/' not in image:
        genre_image = os.path.join(control.OTAKU_GENRE_PATH, image)
        art_image = os.path.join(control.OTAKU_ICONS_PATH, image)
        image = genre_image if os.path.exists(genre_image) else art_image
    if fanart and not isinstance(fanart, list) and '/' not in fanart:
        genre_fanart = os.path.join(control.OTAKU_GENRE_PATH, fanart)
        art_fanart = os.path.join(control.OTAKU_ICONS_PATH, fanart)
        fanart = genre_fanart if os.path.exists(genre_fanart) else art_fanart
    if poster and '/' not in poster:
        genre_poster = os.path.join(control.OTAKU_GENRE_PATH, poster)
        art_poster = os.path.join(control.OTAKU_ICONS_PATH, poster)
        poster = genre_poster if os.path.exists(genre_poster) else art_poster
    new_res = {
        'isfolder': isfolder,
        'isplayable': isplayable,
        'name': name,
        'url': url,
        'info': info,
        'cast': cast,
        'image': {
                'poster': poster,
                'icon': image,
                'thumb': image,
                'fanart': fanart,
                'landscape': landscape,
                'banner': banner,
                'clearart': clearart,
                'clearlogo': clearlogo
        }
    }
    return new_res


def parse_view(base, isfolder, isplayable, dub=False):
    if control.settingids.showdub and dub:
        base['name'] += ' [COLOR blue](Dub)[/COLOR]'
        base['info']['title'] = base['name']
    parsed_view = allocate_item(base["name"], base["url"], isfolder, isplayable, base["image"], base["info"], fanart=base.get("fanart"), poster=base["image"], landscape=base.get("landscape"), banner=base.get("banner"), clearart=base.get("clearart"), clearlogo=base.get("clearlogo"))
    if control.settingids.dubonly and not dub:
        parsed_view = None
    return parsed_view


def get_season(titles_list):
    import re
    regexes = [r'season\s(\d+)', r'\s(\d+)st\sseason\s', r'\s(\d+)nd\sseason\s', r'\s(\d+)rd\sseason\s', r'\s(\d+)th\sseason\s']
    s_ids = []
    for regex in regexes:
        s_ids += [re.findall(regex, name, re.IGNORECASE) for name in titles_list]
    s_ids = [s[0] for s in s_ids if s]
    if not s_ids:
        regex = r'\s(\d+)$'
        cour = False
        for name in titles_list:
            if name is not None and (' part ' in name.lower() or ' cour ' in name.lower()):
                cour = True
                break
        if not cour:
            s_ids += [re.findall(regex, name, re.IGNORECASE) for name in titles_list]
    s_ids = [s[0] for s in s_ids if s]
    if not s_ids:
        seasonnum = 1
        try:
            for title in titles_list:
                try:
                    seasonnum = re.search(r' (\d)[ rnt][ sdh(]', f' {title[1]}  ').group(1)
                    break
                except AttributeError:
                    pass
        except AttributeError:
            pass
        s_ids = [seasonnum]
    season = int(s_ids[0])
    if season > 10:
        season = 1
    return season


def format_time(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
