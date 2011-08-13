'''
Created on 09/08/2011

@author: mikel
'''
import xbmc



class MyScriptError(Exception):
    pass


def reload_skin():
    xbmc.executebuiltin("XBMC.ReloadSkin()")
