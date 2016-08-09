import os

from bs4 import BeautifulSoup

class ContentReader:
    def __init__(self):
        pass
    
    def getFilesFromJson(self, fnin):
        fileList = None
        
        with open(fnin, 'r', encoding='utf-8') as fin:
            fileList = eval(fin.read())
        
        return fileList
    
    def getFilesFromFolder(self, folder):
        allFiles = os.listdir(folder)
        
        #fix the case not adding "/"
        if folder[-1] != "/":
            folder += "/"
            
        #fix the case not adding "./"
        if folder[:1] != "./":
            folder = "./" + folder
        
        fileList = []
        
        for file in allFiles:
            if file.endswith('.html'):
                file = folder + file
                fileList.append(file)
        
        return fileList
    
    def getFiles(self, fnin):
        fileList = None
        
        if os.path.isdir(fnin):
            fileList = self.getFilesFromFolder(fnin)
        elif os.path.isfile(fnin):
            fileList = self.getFilesFromJson(fnin)
        else:
            print("Can't find the file/path %s" % fnin)
        
        return fileList
    
    def getURL(self, fnin):
        if not os.path.isfile(fnin):
            print('There is no such DOM file %s' % fnin)
            return None
            
        urlFile = fnin.replace(".html", ".url")
        
        if not os.path.isfile(urlFile):
            print('There is no such URL file %s' % urlFile)
            return None
        
        with open(urlFile, "r", encoding='utf-8') as fin:
            #here get the final URL
            url = fin.read().split('\n')[1]
            #if you want get the first URL, you can uncomment here
            #url = fin.read().split('\n')[0]
        
        return url
    
    def loadSoap(self, fnin):
        soup = None
        with open(fnin, "r", encoding='utf-8') as fin:
            content = fin.read()
            soup = BeautifulSoup(content, "html.parser")
        
        return soup