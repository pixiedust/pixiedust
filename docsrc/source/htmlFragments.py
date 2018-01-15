from __future__ import print_function
import os
import subprocess
from bs4 import BeautifulSoup


release_date = "2018-01-15"
print ("Generating clean HTML files for IBM DSX docs site...")
print ("OK with release date of", release_date + "?")


# Grab only .rst files in current directory
for fn in os.listdir('.') :
    if os.path.isfile(fn) :
        tmp = os.path.splitext(fn)

        # DSX doesn't need the install documentation.
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

# Build a dictionary from the ditamap, of the format:
  # docsStructure : { parent-page.html : { children : ["child-page.html", ...]},
  #                   child-page.html : { parent : "parent-page.html"},
  #                   ...
  #                 }  
fh = open('clean-for-dsx/pixiedust.ditamap')
data=fh.read()
fh.close()
ditaSoup = BeautifulSoup(data, "lxml")
navHeads = ditaSoup.topicref
docsStructure = {}
docsStructure['index.html'] = {'children' : []}
for child in navHeads.children :
    if child == '\n' :
        continue
    docsStructure['index.html']['children'].append(child['href'])
    ditaParent = child['href']
    docsStructure[ditaParent] = {"children" : []}
    for grandChild in child.contents :
        if grandChild == '\n' :
            continue
        docsStructure[grandChild['href']] = {"parent" : ditaParent}
        docsStructure[ditaParent]["children"].append(grandChild['href'])

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
            attribs.append({"name": "copyright", "content": "&#xA9;Copyright IBM Corporation 2018"})
            attribs.append({"name": "DC.Rights.Owner", "content": "&#xA9;Copyright IBM Corporation 2018"})
            attribs.append({"name": "dcterms.rights", "content": "&#xA9; Copyright IBM Corporation 2016, 2017, 2018"})
            # Update with date of last release note entry
            attribs.append({"name": "DC.date", "content": release_date})
            for entry in attribs :
                new_tag = soup.new_tag("meta", content=entry["content"])
                new_tag["name"] = entry["name"]
                header.append(new_tag)

            # Replace short doc page titles with longer-form titles for DSX to improve searchability.
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
                "1-1-3.html" : "PixieDust release notes 1.1.3",
                "1-1-4.html" : "PixieDust release notes 1.1.4",
                "1-1-5.html" : "PixieDust release notes 1.1.5",
                "1-1-6.html" : "PixieDust release notes 1.1.6"
            }
            if fn in dsxHeadings :
                soup.body.h1.string = dsxHeadings[fn]
                soup.head.title.string = dsxHeadings[fn]
            elif fn not in dsxHeadings : 
                print("Error:", fn, "does not yet have its own entry in dsxHeadings dict.")

            # Write in simple ToC/nav for DSX docs pages.
            # Appends links to child topics within parent-topic HTML pages; likewise, children point back up to their parent.
            new_p = soup.new_tag('p')
            new_h3 = soup.new_tag('h3')
            new_list = soup.new_tag('ul')

            # Add nav from child back to parent topic section
            if 'parent' in docsStructure[fn].keys() :
                new_h3.append("Return to main topic for:")
                new_a = soup.new_tag('a', href=docsStructure[fn]["parent"])
                new_a.append(dsxHeadings[docsStructure[fn]["parent"]])
                new_li = soup.new_tag('li')
                new_li.insert(0, new_a)
                new_list.insert(0, new_li)

            # Add nav from parent down to child sections. "index.html" is a special case.
            if 'children' in docsStructure[fn].keys() :
                if fn == "index.html" :
                    new_h3.append("Documentation main topics:")
                else :
                    new_h3.append("In this PixieDust docs topic:")

                section_children = docsStructure[fn]['children']
                i = 0
                for child in section_children :
                    new_a = soup.new_tag('a', href=section_children[i])
                    new_a.append(dsxHeadings[section_children[i]])
                    new_li = soup.new_tag('li')
                    new_li.insert(0, new_a)
                    new_list.insert(i, new_li)
                    i += 1

                if fn != "index.html" :
                    new_a = soup.new_tag('a', href="index.html")
                    new_em = soup.new_tag('em')
                    new_em.append('Docs home for PixieDust')
                    new_a.append(new_em)
                    new_li = soup.new_tag('li')
                    new_li.insert(0, new_a)
                    new_list.insert(i+1, new_li)

            new_p.insert(0, new_h3)
            new_p.insert(1, new_list)
            soup.body.div.append(new_p)

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

print ("Yeah, dog! Clean HTML for DSX docs.")