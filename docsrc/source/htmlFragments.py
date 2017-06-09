from __future__ import print_function
import os
import subprocess
from bs4 import BeautifulSoup


# Grab only .rst files in current directory
for fn in os.listdir('.') :
     if os.path.isfile(fn) :
        tmp = os.path.splitext(fn)

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

# Fix the HTML files, stripping away <style> tag and extra tag attributes
for fn in os.listdir('clean-for-dsx') :
    filePath = 'clean-for-dsx/'+fn
    
    if os.path.isfile(filePath) :
        tmp = os.path.splitext(fn)

        if tmp[1] == ".html" :
            fh = open(filePath)
            data=fh.read()
            fh.close()

            soup = BeautifulSoup(data, "lxml")
            # Remove <style> and <meta>
            to_delete = soup.findAll(['style', 'meta'])
            for element in to_delete :
                element.decompose()

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

            # Add DSX metadata to <head>
            header = soup.head
            attribs = []
            attribs.append({"name": "copyright", "content": "&#xA9;Copyright IBM Corporation 2017"})
            attribs.append({"name": "DC.Rights.Owner", "content": "&#xA9;Copyright IBM Corporation 2017"})
            attribs.append({"name": "dcterms.rights", "content": "&#xA9; Copyright IBM Corporation 2016, 2017"})
            # Update with date of last release note entry
            attribs.append({"name": "DC.date", "content": "2017-06-05"})
            for entry in attribs :
                new_tag = soup.new_tag("meta", content=entry["content"])
                new_tag["name"] = entry["name"]
                header.append(new_tag)

            # Write the updated soup
            fh = open(filePath, 'w')
            fh.write(soup.prettify().encode("utf-8"))
            fh.close()

            # Fix the soup's stupidly escaped ampersands within strings
            fh = open(filePath, 'r')
            post_soup = fh.read()
            fh.close()
            updated_soup = post_soup.replace("&amp;#xA9;", "&#xA9;")
            fh = open(filePath, 'w')
            fh.write(updated_soup)
            fh.close()

print ("Yeah, dog!")