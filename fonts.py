'''
Created on 09/08/2011

@author: mikel
'''
import os
import xbmc
import shutil
from utils import SkinUtilsError, check_skin_writability, reload_skin, try_remove_file
import elementtree.ElementTree as ET



class FontXmlError(SkinUtilsError):
    pass



class FontManager:
    __installed_names = None
    __installed_fonts = None
    __font_xml_docs = None
    
    
    def __init__(self):
        check_skin_writability()
        self.__installed_names = []
        self.__installed_fonts = []
    
    
    def _build_font_xml_dict(self):
        font_xml_list = {}
        skin_path = xbmc.translatePath("special://skin/")
        
        #Go into each dir. Could be 720, 1080...
        for dir_item in os.listdir(skin_path):
            dir_path = os.path.join(skin_path, dir_item)
            if os.path.isdir(dir_path):
                #Try with font.xml
                file = os.path.join(dir_path, "font.xml")
                if os.path.isfile(file):
                    font_xml_list[file] = None
                
                #Don't try the next step on windows, wasted time
                if os.name != "nt":
                    file = os.path.join(dir_path, "Font.xml")
                    if os.path.isfile(file):
                        font_xml_list[file] = None
        
        return font_xml_list
    
    
    def _get_font_xml_docs(self):
        if self.__font_xml_docs is None:
            self.__font_xml_docs = self._build_font_xml_dict()
        
        return self.__font_xml_docs
    
    
    def _get_font_xml_file(self, file):
        font_xml_docs = self.__font_xml_docs
        
        if file in font_xml_docs and font_xml_docs[file] is None:
            font_xml_docs[file] = ET.parse(file)
        
        return font_xml_docs[file]
    
    
    def is_name_installed(self, name):
        return name in self.__installed_names
    
    
    def is_font_installed(self, file):
        return file in self.__installed_fonts
    
    
    def _get_font_attr(self, node, name):
        attrnode = node.find(name)
        if attrnode is not None:
            return attrnode.text
    
    
    def _copy_font_file(self, file):
        skin_font_path = xbmc.translatePath("special://skin/fonts/")
        file_name = os.path.basename(file)
        dest_file = os.path.join(skin_font_path, file_name)
        
        #TODO: Unix systems could use symlinks
        
        #Check if it's already there
        if dest_file not in self.__installed_fonts:
            self.__installed_fonts.append(dest_file)
            
            #Overwrite if file exists
            shutil.copyfile(file, dest_file)
    
    
    def install_file(self, path, font_path, commit=True):
        print "user file: %s" % path
        tree = ET.parse(path)
        
        #Handle only the first fontset
        fontset = tree.getroot().find("fontset")
        if fontset:
            #Every font definition inside it
            for item in fontset.findall("font"):
                name = self._get_font_attr(item, "name")
                if name is None:
                    raise FontXmlError("Malformed XML: No name for font definition.")
                
                elif not self.is_name_installed(name):
                    self.add_font(
                        name,
                        os.path.join(font_path, self._get_font_attr(item, "filename")),
                        self._get_font_attr(item, "size"),
                        self._get_font_attr(item, "style"),
                        self._get_font_attr(item, "aspect"),
                        self._get_font_attr(item, "linespacing")
                    )
            
            #If save was requested
            if commit:
                self.commit()
    
    
    def _add_font_attr(self, fontdef, name, value):
        attr = ET.SubElement(fontdef, name)
        attr.text = value
        attr.tail = "\n\t\t\t"
        return attr
    
    
    def add_font(self, name, filename, size, style="", aspect="", linespacing=""):
        font_xml_files = self._get_font_xml_docs().keys()
        
        #Unlikely to happen, but who knows...
        if len(font_xml_files) == 0:
            xbmc.log("Cannot add_font(). Current skin has no font definition files!")
        
        elif self.is_name_installed(name):
            xbmc.log("Font name '%s' was already installed, skipping." % name)
        
        else:
            #Add it to the registry
            self.__installed_names.append(name)
            
            #Iterate over all skin font files
            for font_xml in font_xml_files:
                print "font file:  %s" % font_xml
                font_doc = self._get_font_xml_file(font_xml)
                root = font_doc.getroot()
                
                #Iterate over all the fontsets on the file
                for fontset in root.findall("fontset"):
                    fontset.findall("font")[-1].tail = "\n\t\t"
                    fontdef = ET.SubElement(fontset, "font")
                    fontdef.text, fontdef.tail = "\n\t\t\t", "\n\t"
                    
                    self._add_font_attr(fontdef, "name", name)
                    
                    #We get the full file path to the font, so let's basename
                    self._add_font_attr(fontdef, "filename", os.path.basename(filename))
                    self._copy_font_file(filename)
                    
                    last = self._add_font_attr(fontdef, "size", size)
                    
                    if style:
                        if style in ["normal", "bold", "italics", "bolditalics"]:
                            last = self._add_font_attr(fontdef, "style", style)
                        
                        else:
                            raise FontXmlError(
                                "Font '%s' has an invalid style definition: %s"
                                % (name, style)
                            )
                    
                    if aspect:
                        last = self._add_font_attr(fontdef, "aspect", aspect)
                    
                    if linespacing:
                        last = self._add_font_attr(fontdef, "linespacing", linespacing)
                    
                    last.tail = "\n\t\t"
    
    
    def commit(self):
        for file,doc in self._get_font_xml_docs().items():
            doc.write(file)
    
    
    def remove_font(self, name):
        pass
    
    
    def remove_installed_names(self, commit=True):
        for font_doc in self._get_font_xml_docs().values():
            root = font_doc.getroot()
            for fontset in root.findall("fontset"):
                for fontdef in fontset.findall("font"):
                    name = self._get_font_attr(fontdef, "name")
                    if name in self.__installed_names:
                        fontset.remove(fontdef)
        
        if commit:
            self.commit()
    
    
    def remove_installed_fonts(self):
        for item in self.__installed_fonts:
            if not try_remove_file(item):
                xbmc.log(
                    "Failed removing font file '%s'. XBMC may still be using it.",
                    xbmc.LOGWARNING
                )
    
    
    def __del__(self):
        self.remove_installed_names()
        
        #Reload skin so font files are no longer in use
        #reload_skin()
        self.remove_installed_fonts()
