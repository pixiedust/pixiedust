from __future__ import print_function
import os
import subprocess
from bs4 import BeautifulSoup

print ("Generating clean HTML files for IBM DSX docs site...")

# Grab only .rst files in current directory
for fn in os.listdir('.') :
    if os.path.isfile(fn) :
        tmp = os.path.splitext(fn)
        ditaSoup = None
        dsxFormat = {}

        # This if and corresponding HTML piece below are a quick fix to ignore 1.6 instructions I manually updated for Inge.
        if tmp[0] == "install":
            print ("Skipped .rst: " + tmp[0])
            continue
        if tmp[1] == ".rst" :
            source = fn
            parsed = (tmp[0]+"-tmp.rst")
            dest = ("clean-for-dsx/"+tmp[0]+".html")
            fh = open(source)
            writeOut = open(parsed, 'w+')

            for line in fh :
                words = line.split()
                if ("container::" or "raw::" or "note::") in words :
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

        if tmp[0] == "install":
            print ("Skipped .html: " + tmp[0])
            continue
        if tmp[1] == ".ditamap" :
            subprocess.call(["find", "clean-for-dsx/", "-iname", "pixiedust.ditamap", "-exec", "cp", "{}", '../build/html', ";"])
            print ("Copied " + filePath + " to ../build/html directory.")

            # Build a dictionary from the ditamap, of the format:
            # dsxFormat : { parent-page.html : { children : [...]},
            #               child-page.html : { parent : "parent-page.html"}
            #               ...
            #              }  
            fh = open(filePath)
            data=fh.read()
            fh.close()
            ditaSoup = BeautifulSoup(data, "lxml")
            navHeads = ditaSoup.topicref
            for child in navHeads.children :
                if child == '\n' :
                    continue
                ditaParent = child['href']
                dsxFormat[ditaParent] = {"children" : []}
                for grandChild in child.contents :
                    if grandChild == '\n' :
                        continue
                    #dsxFormat[grandChild['href']] = {"parent" : ditaParent}
                    dsxFormat[ditaParent]["children"].append(grandChild['href'])

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
                if tag.get("class") and ("admonition" in tag.get("class") and "note" in tag.get("class")) :
                    tag.name = "blockquote"
                    tag.attrs = {}
                    continue
                if tag.get("class") and ("admonition-title" in tag.get("class")) :
                    tag.name = "strong"
                    tag.attrs = {}
                    continue
                if tag is not None and (tag.get("src") or tag.get("href")) :
                    if tag.name == "img" :
                        prePath = "https://raw.githubusercontent.com/ibm-cds-labs/pixiedust/master/docs/"
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
            attribs.append({"name": "DC.date", "content": "2017-12-01"})
            for entry in attribs :
                new_tag = soup.new_tag("meta", content=entry["content"])
                new_tag["name"] = entry["name"]
                header.append(new_tag)

            # Replace short doc page titles with longer-form titles for DSX to improve searchability.
            ##origHeading = soup.body.h1.string
            dsxHeadings = {
                "index.html" : "Welcome to PixieDust",
                # Use PixieDust section
                "use.html" : "Use PixieDust",
                "loaddata.html" : "Load Data with PixieDust",
                "displayapi.html" : "Display Data Using PixieDust",
                "packagemanager.html" : "Use PixieDust to Manage Packages",
                "scalabridge.html" : "Use Scala in a Python Notebook via PixieDust",
                "sparkmonitor.html" : "PixieDust's Spark Progress Monitor",
                "download.html" : "Download Data via PixieDust",
                "logging.html" : "PixieDust Logging",
                # Develop for PixieDust section
                "develop.html" : "Develop for PixieDust",
                "contribute.html" : "Contribute to PixieDust",
                "writeviz.html" : "Write a New PixieDust Visualization",
                "renderer.html" : "Build a PixieDust Renderer",
                "test.html" : "Test PixieDust In-Development Features",
                # PixieApps section
                "pixieapps.html" : "PixieApps: Use PixieDust to Generate UI Elements",
                "hello-world-pixieapp.html" : "Hello World PixieApp",
                "reference-pixieapp.html" : "Configuring PixieApp Routes",
                "html-attributes-pixieapp.html" : "Custom HTML Attributes for PixieApps",
                "custom-elements-pixieapp.html" : "Custom Elements for PixieApps",
                "dynamic-values-pixieapp.html" : "Dynamic Values and User Input with PixieApps",
                "create-widget-pixieapp.html" : "Creating a PixieApp Widget to Reuse UI Elements",
                "hello-world-data-pixieapp.html" : "Hello World PixieApp with Data",
                # PixieGateway section
                "pixiegateway.html" : "PixieGateway: A Web Server for PixieApps and PixieDust Charts",
                "install-pixiegateway.html" : "Install PixieGateway",
                "chart-sharing.html" : "PixieDust Chart Sharing",
                "pixieapp-publishing.html" : "PixieApp Publishing to the Web",
                # Release Notes section
                "releasenotes.html" : "PixieDust Release Notes",
                "1-0-4.html" : "PixieDust release notes 1.0.4",
                "1-0-5.html" : "PixieDust release notes 1.0.5",
                "1-0-6.html" : "PixieDust release notes 1.0.6",
                "1-0-7.html" : "PixieDust release notes 1.0.7",
                "1-0-8.html" : "PixieDust release notes 1.0.8",
                "1-0-9.html" : "PixieDust release notes 1.0.9",
                "1-0-10.html" : "PixieDust release notes 1.0.10",
                "1-0-11.html" : "PixieDust release notes 1.0.11",
                "1-1.html" : "PixieDust release notes 1.1",
                "1-1-1.html" : "PixieDust release notes 1.1.1",
                "1-1-2.html" : "PixieDust release notes 1.1.2",
                "1-1-3.html" : "PixieDust release notes 1.1.3"
            }
            if fn in dsxHeadings :
                soup.body.h1.string = dsxHeadings[fn]
                soup.head.title.string = dsxHeadings[fn]
            elif fn not in dsxHeadings : 
                print("Error:", fn, "does not yet have its own entry in dsxHeadings dict.")

# TODO: append links to child topics within parent-topic HTML pages.

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

print ("Yeah, dog! Clean HTML.")