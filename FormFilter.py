import re

from pprint import pprint
from collections import defaultdict
from ContentReader import ContentReader

class FormFilter:
    def __init__(self):
        self.wordList = ['account', 'visa', 'credit', 'card', 'master', 'bank', 'banking', 'customer', 'client', 'country', 'user', 'email', 'userid', 'username', 'number', 'city']
        
        self.cr = ContentReader()
    
    def checkForm(self, fnin):
        soup = self.cr.loadSoap(fnin)
        
        if not soup:
            return "noform"
        
        for form in soup.find_all("form"):
            
            inputElems = form.find_all("input")
            
            hasInput = False
            
            for elem in inputElems:
                hasInput = True
                formType = elem.get('type', '').lower()
                
                if formType == 'password':
                    return "form"
            
            #if no input element found, go to next form
            if not hasInput:
                continue
            
            #check whether include sensitive words in form
            formContent = form.get_text().lower()
        
            for word in re.findall(r"[\w']*", formContent):
                for sword in self.wordList:
                    if sword in word:
                        return "form"
        
        return "noform"
    
    def sensitiveFormFilter(self, fnin, fnout):
        fileList = self.cr.getFiles(fnin)
        
        if not fileList:
            return
        
        res = defaultdict(list)
        
        for file in fileList:
            flag = self.checkForm(file)
            res[flag].append(file)
        
        #output to files
        for flag, files in res.items():
            fname = fnout + "_" + flag
            with open(fname, "w", encoding="utf-8") as fout:
                pprint(files, fout)

if __name__ == '__main__':   
    ff = FormFilter()
    ff.sensitiveFormFilter('./filelist_removevecdup', "filelist")