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


def debug_log(msg):
    xbmc.log(msg, xbmc.LOGDEBUG)


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


def get_current_skin_path():
    return os.path.normpath(xbmc.translatePath("special://skin/"))


def get_skin_name():
    return os.path.basename(get_current_skin_path())


def get_local_skin_path():
    user_addons_path = xbmc.translatePath("special://home/addons")
    return os.path.normpath(
        os.path.join(user_addons_path, get_skin_name())
    )


def copy_skin_to_userdata():
    #Warn user before doing this weird thing
    d = xbmcgui.Dialog()
    msg1 = "This addon needs to install some extra resources."
    msg2 = "This installation requires a manual XBMC restart."
    msg3 = "Begin installation now? After that it will exit."
    
    if not d.yesno("Notice", msg1, msg2, msg3):
        sys.exit(1)
    
    else:
        #Get skin dest name
        local_skin_path = get_local_skin_path()
        
        #If it was not copied before...
        if not os.path.exists(local_skin_path):
            shutil.copytree(get_current_skin_path(), local_skin_path)
            #xbmc.executebuiltin("RestartApp")
            sys.exit(1)


#Skin was copied but XBMC was not restarted
def check_needs_restart():
    #Get skin paths
    current_skin_path = get_current_skin_path()
    local_skin_path = get_local_skin_path()
    
    #Local skin exists and does not match current skin path, restart.
    if os.path.isdir(local_skin_path) and current_skin_path != local_skin_path:
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


def skin_is_local():
    return get_current_skin_path() == get_local_skin_path()


def check_skin_writability():
    #Some debug info
    debug_log("-- skinutils debug info --")
    debug_log("current skin path: %s\n" % get_current_skin_path())
    debug_log("local path should be: %s" % get_local_skin_path())
    
    #Check if XBMC needs a restart
    check_needs_restart()
    
    #Get the current skin's path
    skin_path = get_current_skin_path()
    
    #Check if it's local or not (contained in userdata)
    if not skin_is_local():
        copy_skin_to_userdata()
    
    #Check if this path is writable
    elif not os.access(skin_path, os.W_OK) or not do_write_test(skin_path):
        d = xbmcgui.Dialog()
        d.ok("Fatal Error", "Skin directory is not writable.")
        sys.exit(2)


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
