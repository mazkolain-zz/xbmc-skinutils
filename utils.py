'''
Created on 09/08/2011

@author: mikel
'''
import os
import sys
import time
import xbmc, xbmcgui
import shutil



class MyScriptError(Exception):
    pass


def reload_skin():
    xbmc.executebuiltin("XBMC.ReloadSkin()")


def try_remove_file(file, wait=0.5, tries=10):
    removed = False
    num_try = 0
    
    while num_try < tries and not removed:
        try:
            os.remove(file)
            return True
        
        except OSError:
            num_try += 1
            time.sleep(wait)
    
    return False


def check_skin_writability():
    skin_path = xbmc.translatePath("special://skin/")
    if not os.access(skin_path, os.W_OK):
        #Get user profile's addon folder
        user_addons_path = xbmc.translatePath("special://home/addons")
        
        #Remove end slash with normpath()
        skin_name = os.path.basename(os.path.normpath(skin_path))
        
        #Build skin dest name
        skin_dest_path = os.path.join(user_addons_path, skin_name)
        
        #Warn user before doing this weird thing
        d = xbmcgui.Dialog()
        msg1 = "The current skin needs to be writable."
        msg2 = "Choosing yes will restart xbmc after a few seconds."
        msg3 = "After that, try running this addon again."
        
        if not d.yesno("Notice", msg1, msg2, msg3):
            sys.exit(1)
        
        else:
            #If it was not copied before...
            if not os.path.exists(skin_dest_path):
                shutil.copytree(skin_path, skin_dest_path)
                xbmc.executebuiltin("RestartApp")
