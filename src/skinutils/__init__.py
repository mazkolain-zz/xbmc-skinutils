'''
Created on 09/08/2011

@author: mikel
'''
__all__ = ["fonts", "includes"]


import os
from os import listdir
from os.path import isdir, isfile, dirname, basename
import sys
import time
import xbmc, xbmcgui
import shutil
import re



class SkinUtilsError(Exception):
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


def case_file_exists(file):
    if not os.path.isfile(file):
        return False
    
    else:
        file_dir = dirname(file)
        if not isdir(file_dir):
            return False
        
        else:
            dir_contents = listdir(file_dir)
            return basename(file) in dir_contents


def copy_skin_to_userdata():
    #Get the skin's path
    skin_path = xbmc.translatePath("special://skin/")
    
    #Get user profile's addon folder
    user_addons_path = xbmc.translatePath("special://home/addons")
    
    #Remove end slash with normpath()
    skin_name = os.path.basename(os.path.normpath(skin_path))
    
    #Build skin dest name
    skin_dest_path = os.path.join(user_addons_path, skin_name)
    
    #Warn user before doing this weird thing
    d = xbmcgui.Dialog()
    msg1 = "This addon needs to install some extra resources."
    msg2 = "This installation requires a manual XBMC restart."
    msg3 = "Begin installation now? After that it will exit."
    
    if not d.yesno("Notice", msg1, msg2, msg3):
        sys.exit(1)
    
    else:
        #If it was not copied before...
        if not os.path.exists(skin_dest_path):
            shutil.copytree(skin_path, skin_dest_path)
            #xbmc.executebuiltin("RestartApp")
            sys.exit(1)


#Skin was copied but XBMC was not restarted
def check_needs_restart():
    #Get the skin's path
    skin_path = os.path.normpath(xbmc.translatePath("special://skin/"))
    
    #Remove end slash with normpath()
    skin_name = os.path.basename(os.path.normpath(skin_path))
    
    #Get user profile's addon folder
    user_addons_path = xbmc.translatePath("special://home/addons")
    
    #Build skin dest name
    skin_dest_path = os.path.normpath(
        os.path.join(user_addons_path, skin_name)
    )
    
    #Dest path exists and does not match current skin path, restart.
    if os.path.isdir(skin_dest_path) and skin_path != skin_dest_path:
        d = xbmcgui.Dialog()
        d.ok("Notice", "Restart XBMC to complete the installation.")
        sys.exit(1)


def do_write_test(path):
    test_file = os.path.join(path, 'write_test.txt')
    
    try:
        #Open and cleanup
        open(test_file,'a').close()
        os.remove(test_file)
        return True
    
    except Exception:
        return False


def check_skin_writability():
    #Check if XBMC needs a restart
    check_needs_restart()
    
    #Get the current skin's path
    skin_path = xbmc.translatePath("special://skin/")
    
    #Check if it's not writable at all
    if not os.access(skin_path, os.W_OK):
        copy_skin_to_userdata()
    
    #Vista's UAC may be lying to us. Do a real write operation
    elif not do_write_test(skin_path):
        copy_skin_to_userdata()


def make_backup(path):
    backup_path = path + '~'
    #If the backup already exists, don't overwrite it
    if not os.path.exists(backup_path):
        shutil.copy(path, backup_path)


def restore_backup(path):
    backup_path = path + '~'
    #Do nothing if no backup exists
    if os.path.exists(backup_path):
        os.remove(path)
        os.rename(backup_path, path)


def has_invalid_xml_comments(contents):
    pattern = re.compile('<!--(.*?)-->', re.MULTILINE | re.DOTALL)
    group_pattern = re.compile('^-|--|-$')
    for match in re.finditer(pattern, contents):
        if re.match(group_pattern, match.group(1)) is not None:
            return True


def sanitize_xml(file, contents):
    p = re.compile('<!--.*?-->', re.MULTILINE | re.DOTALL)
    clean_contents, num_repl = re.subn(p, '', contents)
    open(file, 'w').write(clean_contents)


def check_file_sanity(file):
    contents = open(file, 'r').read()
        
    #Check if the file has invalid comments
    if has_invalid_xml_comments(contents):
        make_backup(file)
        sanitize_xml(file, contents)
