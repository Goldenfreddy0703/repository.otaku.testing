from resources.lib.ui import control
import xbmc


class SettingsMonitor(xbmc.Monitor):
    def __init__(self):
        while not self.abortRequested():
            xbmc.sleep(1000)

    # @staticmethod
    # def onSettingsChanged():
