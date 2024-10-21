class BrowserBase:
    _BASE_URL = None

    @staticmethod
    def _clean_title(text):
        return text.replace(u'×', ' x ')

    @staticmethod
    def _sphinx_clean(text):
        text = text.replace('+', r'\+')
        text = text.replace('-', r'\-')
        text = text.replace('!', r'\!')
        text = text.replace('^', r'\^')
        text = text.replace('"', r'\"')
        text = text.replace('~', r'\~')
        text = text.replace('*', r'\*')
        text = text.replace('?', r'\?')
        text = text.replace(':', r'\:')
        return text

    @staticmethod
    def embeds():
        return ['doodstream', 'filelions', 'filemoon', 'hd-2', 'iga', 'kwik',
         'megaf', 'moonf', 'mp4upload', 'mp4u', 'mycloud', 'streamtape',
         'streamwish', 'vidcdn', 'vidplay', 'vidstream', 'yourupload', 'zto']
