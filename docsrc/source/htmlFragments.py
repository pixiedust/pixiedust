from __future__ import print_function
import os
import subprocess
from bs4 import BeautifulSoup


# Grab only .rst files in current directory
for fn in os.listdir('.') :
     if os.path.isfile(fn) :
        tmp = os.path.splitext(fn)
        # ('fn', '.rst')

        if tmp[1] == ".rst" :
            source = fn
            parsed = (tmp[0]+"-tmp.rst")
            dest = ("clean-for-dsx/"+tmp[0]+".html")
            fh = open(source)
            writeOut = open(parsed, 'w+')

            for line in fh :
                words = line.split()
                if ("container::" or "raw::") in words :
                    continue
                if source == "index.rst" and (("Get" in words and "Started" in words) or "-----------" in words) :
                    continue
                if "toctree::" in words :
                    break
                else :
                    print (line, end='', file=writeOut,)

            fh.close()
            writeOut.close()
            subprocess.call(['rst2html5.py', parsed, dest])
            subprocess.call(['rm', parsed])

# Now fix the HTML files, stripping away <style> tag and extra tag attributes
for fn in os.listdir('clean-for-dsx') :
    filePath = 'clean-for-dsx/'+fn
    
    if os.path.isfile(filePath) :
        tmp = os.path.splitext(fn)

        if tmp[1] == ".html" :
            fh = open(filePath)
            data=fh.read().replace('\n', '')
            fh.close()

            soup = BeautifulSoup(data, "lxml")
            # Remove style elements
            to_extract = soup.findAll('style')
            for element in to_extract :
                element.extract()

            # Remove all tag attributes except for src and href; except for <span> edge-case for code blocks
            for tag in soup.findAll(True) :
                if tag.get("class") and ("docutils" in tag.get("class") and "literal" in tag.get("class")) :
                        tag.name = "code"
                        tag.attrs = {}
                        continue
                if tag is not None and (tag.get("src") or tag.get("href")) :
                    if tag.name == "img" :
                        prePath = "../../../docs/"
                        fixedURL = prePath + tag.get("src")
                        tag["src"] = fixedURL
                    if tag.get("class") :
                        del tag["class"]
                    continue
                # Base case: remove all attributes
                tag.attrs = {}

            fh = open(filePath, 'w')
            fh.write(soup.prettify().encode("utf-8"))
            fh.close()

print ("Yeah, dog!")