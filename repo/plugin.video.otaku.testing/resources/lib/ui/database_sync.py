import xbmcvfs
import threading

from resources.lib.ui import control
from sqlite3 import dbapi2, version

database_path = control.malSyncDB
sqlite_version = version


class MalSyncDatabase:
    def __init__(self):
        self.activites = None

        self.build_sync_activities()
        self.build_show_table()
        self.build_showmeta_table()
        self.build_episode_table()
        self.build_show_data_table()

        # If you make changes to the required meta in any indexer that is cached in this database
        # You will need to update the below version number to match the new addon version
        # This will ensure that the metadata required for operations is available
        # You may also update this version number to force a rebuild of the database after updating Otaku
        self.last_meta_update = '1.0.0'
        threading.Lock().acquire()
        self.refresh_activites()
        self.check_database_version()

    def refresh_activites(self):
        cursor = self.get_cursor()
        cursor.execute('SELECT * FROM activities WHERE sync_id=1')
        self.activites = cursor.fetchone()
        cursor.close()

    def set_base_activites(self):
        cursor = self.get_cursor()
        cursor.execute('INSERT INTO activities(sync_id, otaku_version) VALUES(1, ?)', (self.last_meta_update,))
        cursor.connection.commit()
        cursor.close()

    def check_database_version(self):
        if not self.activites or self.activites.get('otaku_version') != self.last_meta_update:
            self.re_build_database(True)

    def build_show_table(self):
        threading.Lock().acquire()
        cursor = self.get_cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS shows (mal_id INTEGER PRIMARY KEY, '
                       'anilist_id INTEGER,'
                       'simkl_id INTEGER,'
                       'kitsu_id INTEGER,'
                       'kodi_meta BLOB NOT NULL, '
                       'anime_schedule_route TEXT NOT NULL, '
                       'UNIQUE(mal_id))')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS ix_shows ON "shows" (mal_id ASC )')
        cursor.connection.commit()
        cursor.close()
        control.try_release_lock(threading.Lock())

    def build_showmeta_table(self):
        threading.Lock().acquire()
        cursor = self.get_cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS shows_meta (mal_id INTEGER PRIMARY KEY, '
                       'meta_ids BLOB,'
                       'art BLOB, '
                       'UNIQUE(mal_id))')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS ix_shows_meta ON "shows_meta" (mal_id ASC )')
        cursor.connection.commit()
        cursor.close()
        control.try_release_lock(threading.Lock())

    def build_show_data_table(self):
        threading.Lock().acquire()
        cursor = self.get_cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS show_data (mal_id INTEGER PRIMARY KEY, '
                       'data BLOB NOT NULL, '
                       'last_updated TEXT NOT NULL, '
                       'UNIQUE(mal_id))')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS ix_show_data ON "show_data" (mal_id ASC )')
        cursor.connection.commit()
        cursor.close()
        control.try_release_lock(threading.Lock())

    def build_episode_table(self):
        threading.Lock().acquire()
        cursor = self.get_cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS episodes (mal_id INTEGER NOT NULL, '
                       'season INTEGER NOT NULL, '
                       'kodi_meta BLOB NOT NULL, '
                       'last_updated TEXT NOT NULL, '
                       'number INTEGER NOT NULL, '
                       'filler TEXT, '
                       'FOREIGN KEY(mal_id) REFERENCES shows(mal_id) ON DELETE CASCADE)')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS ix_episodes ON episodes (mal_id ASC, season ASC, number ASC)')
        cursor.connection.commit()
        cursor.close()
        control.try_release_lock(threading.Lock())

    def build_sync_activities(self):
        threading.Lock().acquire()
        cursor = self.get_cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS activities (sync_id INTEGER PRIMARY KEY, otaku_version TEXT NOT NULL)')
        cursor.connection.commit()
        cursor.close()
        control.try_release_lock(threading.Lock())

    @staticmethod
    def get_cursor():
        xbmcvfs.mkdir(control.dataPath)
        conn = dbapi2.connect(database_path, timeout=60.0)
        conn.row_factory = dict_factory
        conn.execute("PRAGMA FOREIGN_KEYS=1")
        cursor = conn.cursor()
        return cursor

    def re_build_database(self, silent=False):
        import service

        if not silent:
            confirm = control.yesno_dialog(control.ADDON_NAME, control.lang(30032))
            if confirm == 0:
                return

        service.update_mappings_db()
        service.update_dub_json()

        with open(control.malSyncDB, 'w'):
            pass

        self.build_sync_activities()
        self.build_show_table()
        self.build_showmeta_table()
        self.build_episode_table()
        self.build_show_data_table()

        self.set_base_activites()
        self.refresh_activites()
        if not silent:
            control.notify(f'{control.ADDON_NAME}: Database', 'Metadata Database Successfully Cleared', sound=False)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d