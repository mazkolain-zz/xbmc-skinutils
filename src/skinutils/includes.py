'''
Created on 09/08/2011

@author: mikel
'''
import os
import xbmc
import elementtree.ElementTree as ET
from skinutils import SkinUtilsError, check_skin_writability, make_backup, restore_backup, case_file_exists



class IncludeXmlError(SkinUtilsError):
    pass



class IncludeManager:
    __installed_names = None
    __includes = None
    
    
    def __init__(self):
        check_skin_writability()
        self.__installed_names = []
    
    
    def _locate_includes(self):
        include_list = {}
        skin_path = xbmc.translatePath("special://skin/")
        
        #Go into each dir. Could be 720, 1080...
        for dir_item in os.listdir(skin_path):
            dir_path = os.path.join(skin_path, dir_item)
            if os.path.isdir(dir_path):
                file = os.path.join(dir_path, "includes.xml")
                if case_file_exists(file):
                    include_list[file] = None
                
                file = os.path.join(dir_path, "Includes.xml")
                if case_file_exists(file):
                    include_list[file] = None
        
        return include_list
    
    
    def _get_includes(self):
        if self.__includes is None:
            self.__includes = self._locate_includes()
        
        return self.__includes
    
    
    def _get_include_xml(self, file):
        if file in self.__includes and self.__includes[file] is None:
            self.__includes[file] = ET.parse(file)
        
        return self.__includes[file]
    
    
    def is_name_installed(self, name):
        return name in self.__installed_names
    
    
    def add_include(self, name, node):
        for item in self._get_includes().keys():
            doc = self._get_include_xml(item)
            doc.getroot().append(node)
            self.__installed_names.append(name)
    
    
    def install_file(self, file, commit=True):
        print "install include: %s" % file
        tree = ET.parse(file)
        
        #Handle all includes
        for item in tree.getroot().findall("include"):
            name = item.get("name")
            if name is None:
                xbmc.log("Only named includes are supported.", xbmc.LOGWARNING)
            
            elif self.is_name_installed(name):
                xbmc.log("Include name '%s' already installed" % name)
            
            else:
                self.add_include(name, item)
        
        if commit:
            self.commit()
    
    
    def commit(self):
        for xml_file, doc in self._get_includes().items():
            make_backup(xml_file)
            doc.write(xml_file)
    
    
    def remove_installed_names(self, commit=True):
        for xml_file in self._get_includes().keys():
            restore_backup(xml_file)
    
    
    def __del__(self):
        self.remove_installed_names()
