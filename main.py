import sys
import re
from pprint import pprint as pp
from difflib import SequenceMatcher as matcher

# Manupulate a configuration file with special needs (Unreal Engine 3 config file).
# Each option section can have duplicate options with different values.
# No syntax is checked.
# Excepting structure in config file: 
#   [Option.Section/OptionSection]
#   Option=Value#Comment
#   //Option=Value
#   Option=2222;Comment
#   Option=
# Excepting duplicate options are in a sequence.  
# Options in a section stored as a list of tuples.
# Dict structure:
#   self.sections["OptionSection"][tuple("option1", "value1", "comment1"), tuple("option2", "value2", ""), ...]
# Operations:
#   - Parse a config file.ini in to a dict structure including comments [# ; //]
#   - Create a tuple out of a raw config file string 
#   - Set existing options if present. If not present, don't set but print similar options in that section.
#   - Create option(s) in a section at a given index
#   - Create a new section with options (except list())
#   - Delete option in section, or whole section
#   - Write present structure to the same file or a new one  


class Config():
    
    def __init__(self, path):    
        self.configList = list()
        self.path = path
        self.commentDelimeters = ["#", ";"]
        with open(path, "rt") as file:
            self.configList = file.readlines()
        self.sections = dict()
        # Regex for option section 
        self.sectionsRE = re.compile("\[[A-Za-z]+\.?[A-Za-z]+?\]")
        self.parse()
    
    def set(self, section, option, value="", comment=""):
        i = 0
        if type(option) == type(tuple()):
            opt, val, com = option
            self.set(section, opt, val, com)
        elif type(option) == type(list()):
            for opt, val, com in option:
                self.set(section, opt, val, com)
        else:
            self.checkPresence(section, option)
            # for i, ovc in enumerate(sel.section[section]):
            #   opt, val, com = ovc      
            for opt, val, com in self.sections[section]:
                if opt == option:
                    # If no comment given, keep existing comment if there is one
                    if comment == "" and com != "":
                        comment = com
                    # Set only comment if no value given
                    if not value and val:
                        value = val
                    self.sections[section][i] = (option, value, comment)
                    break
                i += 1            
    
    def createOption(self, section, option, value="", comment="", index=0):
        if type(option) == type(tuple()):
            opt, val, com = option
            self.sections[section].insert(index, (opt, val, com))
        elif type(option) == type(list()):
            for opt, val, com in option:
                self.sections[section].insert(index, (opt, val, com))
        else:
            self.sections[section].insert(index, (option, value, comment))

    def createSection(self, section, options):
        if section in self.sections:
            print("Section", section, "already exists, section not created")
            return
        else:
            self.sections.update({section:options})
        pass

    def createTuple(self, ConfigLine):
        # Find and strip comment
        # Leftside of the equalsign is an option
        # Rightside of the equalsign is an value
        commentSignIndex = 0
        eqlSignIndex = 0
        comment = ""
        option = ""
        value = ""        
        for delimiter in self.commentDelimeters:
            if delimiter in ConfigLine:
                commentSignIndex = ConfigLine.index(delimiter)
                comment = ConfigLine[commentSignIndex:].strip()
                ConfigLine = ConfigLine.replace(comment, "").strip()
                comment = comment.replace(delimiter, "", 1)                
        try:
            eqlSignIndex = ConfigLine.index("=")
            option = ConfigLine[0:eqlSignIndex].strip()
            value = ConfigLine[eqlSignIndex + 1:].strip()
        except ValueError:
            # No equalsign found, No valid Syntax, check if only comment in
            pass    
        return (option, value, comment)

    def parse(self):
        currentSection = ""
        i = 0
        options = []
        OptionValueComment = tuple()
        
        while i < len(self.configList):
            self.configList[i] = self.configList[i].strip()
            if(self.configList[i] == ""):
                del self.configList[i]
                i -= 1
            i += 1
        
        i = 0
        while i < len(self.configList):
            if re.match(self.sectionsRE, self.configList[i]):
                currentSection = self.configList[i]
                currentSection = currentSection.replace("[", "")
                currentSection = currentSection.replace("]", "")
                try:
                    i += 1
                    if self.configList[i]:
                        pass
                except IndexError:
                    #Except empty option section
                    self.sections.update({currentSection:list()})
                    return
                while i < len(self.configList) and not re.match(self.sectionsRE, self.configList[i]):                       
                    OptionValueComment = self.createTuple(self.configList[i])                                     
                    options.append(OptionValueComment)               
                    i += 1
                self.sections.update({currentSection:options.copy()})
                options.clear()

    def checkPresence(self, section, option):
        if option not in (OVC[0] for OVC in self.sections[section]):
            print("Option", option , "in", section, "not found. Option not set")
            self.doYouMean(section, option)
            return False
        else: 
            return True

    def doYouMean(self, section, falseOption):
        # Search similar Options
        matchRatio = 0.6
        noSimiliar = True   
        for y, x, z in self.sections[section]:
            if (matcher(None, y, falseOption).ratio() >= matchRatio):
                print("Do you mean option", y , "?")
                noSimiliar = False
        if noSimiliar:
            print("No similar options", falseOption, "in", section)
    
    def delete(self, section, option, allOptions=False):
        i = 0
        for opt, val, com in self.sections[section]:
            if option == opt:
                del self.sections[section][i]
                if allOptions == False:
                    return
            i += 1

    def setMultipleOptions(self, section, option, values, offset=0):
        i = 0
        j = 0
        start = 0
        newTuple = tuple()
        if self.checkPresence(section, option):
            for opt, val, com in self.sections[section]:
                if opt == option:
                    if start >= offset and j < len(values):
                        newTuple = (opt, values[j], com)
                        self.sections[section][i] = newTuple
                        j += 1
                    elif j == len(values)-1:
                        return
                    else:
                        start += 1
                i += 1
        else:
            return

    def write(self, path=""):
        if path == "":
            path = self.path

        with open(path, "wt") as file:
            for section, options in self.sections.items():
                file.write("[" + section + "]\n")
                for option, value, comment in options:
                    # Write only comment
                    if option == "" and value == "" and comment != "":
                        file.write("#" + comment + "\n")
                        continue
                    if comment:
                        comment = "#" + comment
                    file.write(option + "=" + value + comment + "\n")
                file.write("\n")


def main():
    o = r"C:\Users\Unicorn\Documents\My Games\Rising Storm 2\ROGame\Config\ROEngine.ini"
    ROEngine = Config(o)
#***********************************************************************************************************
    
    #Testing

    #optlist = [  ("", "", "Set a List of options with values and comments"),
    #            ("Port", "9999", ""),
    #            ("PeerPort", "1111", ""),
    #            ("Game", "Short", "No such option testing"),
    #]
    #
    #optlist2 = [
    #    ("NewOption1", "Value1", "Comment"),
    #    ("NewOption2", "Value2", "" )
    #]
    #
    #rawConfigLine = "Option=23424Value    #Comment"
    #
    #ROEngine.set("Engine.Engine", "NetworkDevice", "Holzmodem", "Set singele Option")# 18
    #ROEngine.set("URL", ("Name", "Player", "Set tuple"))
    #ROEngine.set("URL", optlist)
    #
    #ROEngine.createOption("URL", "NewOption1", "Value1") # Create a single option
    #ROEngine.createOption("URL", ("TUpleOption", "TupleValue", ""))
    #ROEngine.createOption("URL", ROEngine.createTuple(rawConfigLine))
    #ROEngine.createOption("Engine.Engine", optlist2, index=99) # Give an index, if to high, options will be appended
    #
    #ROEngine.createSection("New Section", optlist2)
    #vallist = ["val1", "val2", "val3"]
    #ROEngine.setMultipleOptions("Engine.Engine", "LightComplexityColors", vallist, 1) 
    # Set multiple options at a given offset, with a list of values that will be assigned in that order
#**************************************************************************************************************************************    
    #SystemSettings
    op1 = [
        ("bUseMaxQualityMode","True", ""),
        ("MaxAnisotropy", "16", ""),
        ("MaxMultisamples", "1", ""),
        ("OnlyStreamInTextures", "False", ""),
    ]
    #TextureStreaming
    op2 = [
        ("PoolSize", "99999", ""),
        ("AllowStreamingLightmaps", "False", ""),
        ("UsePriorityStreaming", "False", ""),
        ("bAllowSwitchingStreamingSystem", "False", ""),
        
    ]
    #Core.System
    op3 = [
        ("SizeOfPermanentObjectPool", "4000", "")
    ]
    #Engine.Engine
    op4 = [
        ("bAllowMatureLanguage", "TRUE", ""),
        ("bUseTextureStreaming", "False", ""),
    ]

    ROEngine.set("SystemSettings", op1)
    ROEngine.set("TextureStreaming", op2)
    ROEngine.set("Core.System", op3)
    ROEngine.set("Engine.Engine", op4)
    ROEngine.write()

if __name__ == "__main__":
    main()