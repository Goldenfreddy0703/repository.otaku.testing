import ast
import hashlib
import pickle
import re
import time
import xbmcvfs
import threading

from resources.lib.ui import control
from sqlite3 import OperationalError, dbapi2

lock = threading.Lock()


def get_(function, duration, *args, **kwargs):
    """
    Gets cached value for provided function with optional arguments, or executes and stores the result
    :param function: Function to be executed
    :param duration: Duration of validity of cache in hours
    :param args: Optional arguments for the provided function
    """
    key = hash_function(function, args, kwargs)
    if 'key' in kwargs:
        key += kwargs.pop('key')
    cache_result = cache_get(key)
    if cache_result and is_cache_valid(cache_result['date'], duration):
        return_data = ast.literal_eval(cache_result['value'])
        return return_data

    fresh_result = repr(function(*args, **kwargs))
    cache_insert(key, fresh_result)
    if not fresh_result:
        return cache_result if cache_result else fresh_result
    data = ast.literal_eval(fresh_result)
    return data


def hash_function(function_instance, *args):
    function_name = re.sub(r'.+\smethod\s|.+function\s|\sat\s.+|\sof\s.+', '', repr(function_instance))
    return function_name + generate_md5(args)


def generate_md5(*args):
    md5_hash = hashlib.md5()
    [md5_hash.update(str(arg).encode()) for arg in args]
    return str(md5_hash.hexdigest())


def cache_get(key):
    lock.acquire()
    cursor = get_connection_cursor(control.cacheFile)
    try:
        cursor.execute(f'SELECT * FROM cache WHERE key=?', (key,))
        results = cursor.fetchone()
        cursor.close()
        return results
    except OperationalError:
        cursor.close()
    finally:
        control.try_release_lock(lock)


def cache_insert(key, value):
    lock.acquire()
    cursor = get_connection_cursor(control.cacheFile)
    now = int(time.time())
    try:
        cursor.execute(f'CREATE TABLE IF NOT EXISTS cache (key TEXT, value TEXT, date INTEGER, UNIQUE(key))')
        cursor.execute(f'CREATE UNIQUE INDEX IF NOT EXISTS ix_cache ON cache (key)')
        cursor.execute(f'REPLACE INTO cache (key, value, date) VALUES (?, ?, ?)', (key, value, now))
        cursor.connection.commit()
        cursor.close()
    except OperationalError:
        cursor.close()
    finally:
        control.try_release_lock(lock)


def cache_clear():
    lock.acquire()
    cursor = get_connection_cursor(control.cacheFile)
    try:
        cursor.execute("DROP TABLE IF EXISTS cache")
        cursor.execute("VACUUM")
        cursor.connection.commit()
        control.notify(f'{control.ADDON_NAME}: {control.lang(30030)}', control.lang(30031), time=5000, sound=False)
    except OperationalError:
        cursor.close()
    finally:
        control.try_release_lock(lock)


def is_cache_valid(cached_time, cache_timeout):
    now = int(time.time())
    diff = now - cached_time
    return (cache_timeout * 3600) > diff


def get_connection_cursor(filepath):
    conn = get_connection(filepath)
    return conn.cursor()


def get_connection(filepath):
    xbmcvfs.mkdir(control.dataPath)
    conn = dbapi2.connect(filepath)
    conn.row_factory = _dict_factory
    return conn


def get_db_connection():
    xbmcvfs.mkdir(control.dataPath)
    conn = dbapi2.connect(control.malSyncDB, timeout=60.0)
    conn.row_factory = _dict_factory
    return conn


def get_cursor():
    conn = get_db_connection()
    conn.execute("PRAGMA FOREIGN_KEYS=1")
    cursor = conn.cursor()
    return cursor


def update_show(mal_id, kodi_meta, anime_schedule_route=''):
    lock.acquire()
    cursor = get_cursor()
    try:
        cursor.execute('PRAGMA foreign_keys=OFF')
        cursor.execute('REPLACE INTO shows (mal_id, kodi_meta, anime_schedule_route) VALUES (?, ?, ?)', (mal_id, kodi_meta, anime_schedule_route))
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.connection.commit()
        cursor.close()
    except OperationalError:
        cursor.close()
    finally:
        control.try_release_lock(lock)


def update_show_meta(mal_id, meta_ids, art):
    lock.acquire()
    cursor = get_cursor()
    if isinstance(meta_ids, dict):
        meta_ids = pickle.dumps(meta_ids)
    if isinstance(art, dict):
        art = pickle.dumps(art)
    try:
        cursor.execute('PRAGMA foreign_keys=OFF')
        cursor.execute("REPLACE INTO shows_meta (mal_id, meta_ids, art) VALUES (?, ?, ?)", (mal_id, meta_ids, art))
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.connection.commit()
        cursor.close()
    except OperationalError:
        cursor.close()
    finally:
        control.try_release_lock(lock)


def add_mapping_id(mal_id, column, value):
    lock.acquire()
    cursor = get_cursor()
    cursor.execute('UPDATE shows SET %s=? WHERE mal_id=?' % column, (value, mal_id))
    cursor.connection.commit()
    cursor.close()
    control.try_release_lock(lock)


def update_kodi_meta(mal_id, kodi_meta):
    lock.acquire()
    cursor = get_cursor()
    kodi_meta = pickle.dumps(kodi_meta)
    cursor.execute('UPDATE shows SET kodi_meta=? WHERE mal_id=?', (kodi_meta, mal_id))
    cursor.connection.commit()
    cursor.close()
    control.try_release_lock(lock)


def update_show_data(mal_id, data, last_updated=''):
    lock.acquire()
    cursor = get_cursor()
    data = pickle.dumps(data)
    try:
        cursor.execute('PRAGMA foreign_keys=OFF')
        cursor.execute("REPLACE INTO show_data (mal_id, data, last_updated) VALUES (?, ?, ?)", (mal_id, data, last_updated))
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.connection.commit()
        cursor.close()
    except OperationalError:
        cursor.close()
    finally:
        control.try_release_lock(lock)


def update_episode(mal_id, season, number, update_time, kodi_meta, filler=''):
    lock.acquire()
    cursor = get_cursor()
    try:
        cursor.execute('REPLACE INTO episodes (mal_id, season, kodi_meta, last_updated, number, filler) VALUES (?, ?, ?, ?, ?, ?)', (mal_id, season, kodi_meta, update_time, number, filler))
        cursor.connection.commit()
        cursor.close()
    except OperationalError:
        cursor.close()
    finally:
        control.try_release_lock(lock)


def get_show_data(mal_id):
    lock.acquire()
    cursor = get_connection_cursor(control.malSyncDB)
    db_query = 'SELECT * FROM show_data WHERE mal_id IN (%s)' % mal_id
    cursor.execute(db_query)
    show_data = cursor.fetchone()
    cursor.close()
    control.try_release_lock(lock)
    return show_data


def get_episode_list(mal_id):
    lock.acquire()
    cursor = get_cursor()
    cursor.execute('SELECT* FROM episodes WHERE mal_id=?', (mal_id,))
    episodes = cursor.fetchall()
    cursor.close()
    control.try_release_lock(lock)
    return episodes


def get_episode(mal_id):
    lock.acquire()
    cursor = get_cursor()
    cursor.execute('SELECT* FROM episodes WHERE mal_id=?', (mal_id,))
    episode = cursor.fetchone()
    cursor.close()
    control.try_release_lock(lock)
    return episode


def get_show(mal_id):
    lock.acquire()
    cursor = get_connection_cursor(control.malSyncDB)
    db_query = 'SELECT * FROM shows WHERE mal_id IN (%s)' % mal_id
    cursor.execute(db_query)
    shows = cursor.fetchone()
    cursor.close()
    control.try_release_lock(lock)
    return shows


def get_show_meta(mal_id):
    lock.acquire()
    cursor = get_connection_cursor(control.malSyncDB)
    db_query = 'SELECT * FROM shows_meta WHERE mal_id IN (%s)' % mal_id
    cursor.execute(db_query)
    shows = cursor.fetchone()
    cursor.close()
    control.try_release_lock(lock)
    return shows

def remove_from_database(table, mal_id):
    lock.acquire()
    cursor = get_cursor()
    try:
        cursor.execute(f"DELETE FROM {table} WHERE mal_id=?", (mal_id,))
        cursor.connection.commit()
        cursor.close()
    except OperationalError:
        cursor.close()
    finally:
        control.try_release_lock(lock)


def get_mappings(anime_id, send_id):
    lock.acquire()
    cursor = get_connection_cursor(control.mappingDB)
    cursor.execute(f'SELECT * FROM anime WHERE {send_id}=?', (anime_id,))
    mappings = cursor.fetchall()
    cursor.close()
    control.try_release_lock(lock)
    return mappings[0] if mappings else {}


def getSearchHistory(media_type='show'):
    lock.acquire()
    cursor = get_connection_cursor(control.searchHistoryDB)
    try:
        cursor.execute('CREATE TABLE IF NOT EXISTS show (value TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS movie (value TEXT)')
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_history ON movie (value)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_history ON show (value)")
        cursor.execute("SELECT * FROM %s" % media_type)

        history = cursor.fetchall()
        cursor.close()
        history.reverse()
        history = history[:50]
        filter_ = []
        for i in history:
            if i['value'] not in filter_:
                filter_.append(i['value'])
        return filter_
    except OperationalError:
        cursor.close()
        return []
    finally:
        control.try_release_lock(lock)


def addSearchHistory(search_string, media_type):
    lock.acquire()
    cursor = get_connection_cursor(control.searchHistoryDB)
    try:
        cursor.execute('CREATE TABLE IF NOT EXISTS show (value TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS movie (value TEXT)')
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_history ON movie (value)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_history ON show (value)")
        cursor.execute("REPLACE INTO %s Values (?)" % media_type, (search_string,))
        cursor.connection.commit()
        cursor.close()
    except OperationalError:
        cursor.close()
        return []
    finally:
        control.try_release_lock(lock)


def clearSearchHistory():
    lock.acquire()
    confirmation = control.yesno_dialog(control.ADDON_NAME, "Clear search history?")
    if not confirmation:
        return
    cursor = get_connection_cursor(control.searchHistoryDB)
    try:
        cursor.execute("DROP TABLE IF EXISTS movie")
        cursor.execute("DROP TABLE IF EXISTS show")
        cursor.execute("VACCUM")
        cursor.connection.commit()
        cursor.close()
        control.refresh()
        control.notify(control.ADDON_NAME, "Search History has been cleared", time=5000)
    except OperationalError:
        cursor.close()
        return []
    finally:
        control.try_release_lock(lock)


def remove_search(table, value):
    lock.acquire()
    cursor = get_connection_cursor(control.searchHistoryDB)
    try:
        cursor.execute(f'DELETE FROM {table} WHERE value=?', (value,))
        cursor.connection.commit()
        cursor.close()
        control.refresh()
    except OperationalError:
        cursor.close()
    finally:
        control.try_release_lock(lock)


def _dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
