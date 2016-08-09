import os
import lxml.html
import re
import socket
import time
import hashlib

from bs4 import BeautifulSoup
from pprint import pprint
from collections import defaultdict


class NoiseFilter:
    MINIELEMENT = 4
    IPFlag = "<ip>"
    
    def __init__(self, fcorpus, fip):
        self.tagCorpus = None
        with open(fcorpus, "r", encoding='utf-8') as fin:
            self.tagCorpus = eval(fin.read())
        
        self.ipList = None
        with open(fip, "r", encoding='utf-8') as fin:
            self.ipList = eval(fin.read())
    
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
    
    def getTitle(self, fnin):
        soup = self.loadSoap(fnin)
        
        #fetch title for comparing page
        title = soup.find("title")
        if title:
            title = title.get_text().replace("\n","").lower()
        else:
            title = ""
        
        return title
    
    def checkEmpty(self, fnin):
        soup = self.loadSoap(fnin)
        
        if not soup:
            return "empty"
        
        content = str(soup.find('body'))
        
        page = lxml.html.document_fromstring(content)
        
        tagCnt = 0 
        flag = "noempty"
        
        for element in page.iter():
            attribDict = element.attrib
            elemType = attribDict.get('type', None)
            tag = element.tag
            
            if elemType != 'hidden' and type(tag) == str and tag in self.tagCorpus:
                tagCnt += 1
                
        if tagCnt < self.MINIELEMENT:
            flag = "empty"
        
        return flag
    
    def generateSHA1(self, data):
        byteData = bytes(data, 'utf-8')
        return hashlib.sha1(byteData).hexdigest()
    
    def getHash(self, fnin):
        soup = self.loadSoap(fnin)
        
        if not soup:
            return None
        
        #clear up all the input elements
        for inputElem in soup.find_all('input'):
            value = inputElem.get('value', '')
            
            if value != "":
                inputElem['value'] = ""
        
        data = str(soup).strip()
        data = self.generateSHA1(data)
        
        return data
    
    def getHostname(self, url):
        pattern = re.compile(r'http[s]{0,1}://(.+?)/')
        hostname = pattern.search(url)
        
        if hostname:
            hostname = hostname.group(1)
        else:
            pattern = re.compile(r'http[s]{0,1}://(.+)')
            hostname = pattern.search(url)
            if hostname:
                hostname = hostname.group(1)
            else:
                hostname = ""
        
        #check whether host is just ip
        pattern = re.compile(r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}')
        match = pattern.search(hostname)
        
        if match:
            hostname = self.IPFlag + hostname
        
        #remove the port part
        hostname = hostname.split(':')[0]

        return hostname
    
    def DNSQuery(self, hostname):
        answer = None
        ip = None
        #print("DNS ip %s" % hostname)
        
        #set a timeout value for the DNS socket
        socket.setdefaulttimeout(4)
        
        retryCnt = 3
        
        #retry multiple times to ensure the hostname can't be reached
        while (not answer) and retryCnt:
            try:
                answer = socket.gethostbyname_ex(hostname)
            except socket.timeout:
                retryCnt -= 1
                #print('%s DNS query is timeout' % hostname)
            except (socket.herror, socket.gaierror):
                retryCnt -= 1
                #print("%s can't be resolved" % hostname)
            except:
                retryCnt -= 1
            
            time.sleep(0.1)
            
        if answer:
            ip = answer[2][0]
        else:
            print("<DNS>%s can't be resolved" % hostname)
        
        return ip
    
    def getIP(self, url):
        
        if "https:" in url or "http:" in url:
            hostname = self.getHostname(url)
        else:
            hostname = url
            
        ip = None
        
        #if domain is not IP
        if not hostname.count(self.IPFlag):
            #get ip from file
            if self.ipList:
                ip = self.ipList.get(hostname)
            
            #get ip by DNS query
            if not ip:
                ip = self.DNSQuery(hostname)
                
            if not ip:
                print("Can't find the ip of %s in database" % url)
                return None
        else:
            ip = hostname.split(self.IPFlag)[-1]
        
        if ip == "":
            ip = None
        
        return ip
    
    def hashDuplicate(self, fnin, fnout):
        fileList = self.getFiles(fnin)
        
        if not fileList:
            return
        
        def dictList():
            return defaultdict(list)
        
        hashData = defaultdict(dictList)
        
        #classify file by hash and ip
        for file in fileList:
            hash = self.getHash(file)
            url = self.getURL(file)
            
            if url :
                ip = self.getIP(url)
                if hash and ip:
                    hashData[hash][ip].append(file)
                else:
                    print("No hash or IP case %s" % file)
        
        keepRes = []
        removeRes = []
        
        #output the data
        for hash, fileDict in hashData.items():
            for ip, fileList in fileDict.items():
                keepRes.append(fileList[0])
                removeRes += list(fileList[1:])
        
        keepfn = fnout + "_removedup"
        with open(keepfn, "w", encoding="utf-8") as fout:
            pprint(keepRes, fout)
        
        dupfn = fnout + "_dup"
        with open(dupfn, "w", encoding="utf-8") as fout:
            pprint(removeRes, fout)
        
    def isEmpty(self, fnin, fnout):
        fileList = self.getFiles(fnin)
        
        if not fileList:
            return
        
        res = defaultdict(list)
        
        for file in fileList:
            flag = self.checkEmpty(file)
            res[flag].append(file)
        
        #output to files
        for flag, files in res.items():
            fname = fnout + "_" + flag
            with open(fname, "w", encoding="utf-8") as fout:
                pprint(files, fout)
    
    def isBlocked(self, fnin, fnout):
        fileList = self.getFiles(fnin)
        if not fileList:
            return

        downURL= ['/suspend', '/defaultwebpage']
        downTitle = ['suspended', 'under maintenance']
        
        errURL = ['/404', '/403']
        errTitle = ['404', '403']
        
        res = defaultdict(list)
        
        for file in fileList:
            url = self.getURL(file)
            if url:
            
                title = self.getTitle(file)
                
                flag = "noblock"
                
                #check down cases
                for info in downURL:
                    if url.count(info):
                        flag = "down"
                        continue
                
                for info in downTitle:
                    if title.count(info):
                        flag = "down"
                        continue
                
                #check error cases
                for info in errURL:
                    if url.count(info):
                        flag = "error"
                        continue
                
                for info in errTitle:
                    if title.count(info):
                        flag = "error"
                        continue
                
                res[flag].append(file)
        
        print(len(res))
        
        #output to files
        for flag, files in res.items():
            fname = fnout + "_" + flag
            with open(fname, "w", encoding="utf-8") as fout:
                pprint(files, fout)
                
if __name__ == '__main__':   
    nf = NoiseFilter("HTMLTagsCorpus", "IPFile")
    #nf.isBlocked('./PHISH_ARCHIVE_0706/', 'filelist')
    #nf.isEmpty('./filelist_noblock', 'filelist')
    #nf.hashDuplicate('./filelist_noempty', 'filelist')
