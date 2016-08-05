#!/bin/env python
import os
import json
import urllib2
import requests
import time
import errno
import tarfile
import sys

block_sz = 8192*10

with open('config.json') as config_json:
    config = json.load(config_json)

opcount = 0 #number of requested operations
products = []

#download remote file via urllib2
if "download" in config:
    for file in config["download"]:
        opcount += 1

        dir=file["dir"]
        if not os.path.exists(dir):
            os.makedirs(dir)

        url = file["url"]
        progress_url = os.environ["SCA_PROGRESS_URL"]+".file"+str(len(products));
        requests.post(progress_url, json={"status": "running", "progress": 0, "name": url});
        try:
            u = urllib2.urlopen(url)
            file_name = url.split('/')[-1]
            f = open(dir+'/'+file_name, 'w')
            meta = u.info()

            contentlength = meta.getheaders("Content-Length")
            if len(contentlength) == 1:
                file_size = int(meta.getheaders("Content-Length")[0])
            else:
                file_size = None
                print "Content-Length not set.. can't figure out the final file size"
                print meta

            print "Downloading: %s Bytes: %s" % (file_name, file_size)

            file_size_dl = 0
            progress_time = time.time()
            while True:
                buffer = u.read(block_sz)
                if not buffer:
                    break

                file_size_dl += len(buffer)
                f.write(buffer)

                if time.time() - progress_time > 0.5:
                    if file_size:
                        requests.post(progress_url, json={"progress": float(file_size_dl)/file_size})
                    else:
                        requests.post(progress_url, json={"msg": "Downloaded "+str(file_size_dl)+ " -- total size unknown"})

                    progress_time = time.time()
                    if file_size:
                        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
                    else:
                        status = r"%10d" % (file_size_dl)
                    print status

            requests.post(progress_url, json={"progress": 1, "status": "finished"});
            products.append({"filename": dir+"/"+file_name, "size": file_size_dl})
            f.close()

        except Exception as e:
            print "failed to download "+url
            print e 
            requests.post(progress_url, json={"status": "failed", "msg": str(e)})

#symlink files from local directory to task directory
if "symlink" in config:
    for file in config["symlink"]:
        opcount += 1

        print "Handling symlink request",file["src"]
        src = file["src"]

        progress_url = os.environ["SCA_PROGRESS_URL"]+".symlink"+str(len(products));
        requests.post(progress_url, json={"status": "running", "progress": 0, "name": src});
        try:
            dest = src.split('/')[-1]
            if "dest" in file:
                dest = file["dest"]

            try:
                os.symlink(src, dest)
                requests.post(progress_url, json={"progress": 1, "status": "finished"});
                products.append({"filename": dest})
            except OSError, e:
                if e.errno == errno.EEXIST:
                    os.remove(dest)
                    os.symlink(src, dest)
                    requests.post(progress_url, json={"progress": 1, "status": "finished"});
                    products.append({"filename": dest})

        except Exception as e:
            print "failed to symlink:"+src
            print e 
            requests.post(progress_url, json={"status": "failed", "msg": str(e)})

#create tar file from local directory 
if "tar" in config:
    for file in config["tar"]:
        opcount += 1

        src = file["src"]
        dest = file["dest"]
        print "Handling targz request from",src,"to",dest

        progress_url = os.environ["SCA_PROGRESS_URL"]+".tar"+str(len(products));
        requests.post(progress_url, json={"status": "running", "progress": 0, "name": "tarring "+src+" to "+dest});
        try:

            #taropt can be "gz" or "bz2"..
            taropt = ""
            if "opts" in file:
                taropt = file["opts"]

            #TODO python tarfile is slow - maybe I should just drop to shell to run tar -cf..
            #now create tar file
            tar = tarfile.open(dest, "w:"+taropt)
            tar.add(src, arcname=os.path.basename(src))

            #TODO monitor tar progress and report to progress service

            requests.post(progress_url, json={"progress": 1, "status": "finished"});
            products.append({"filename": dest})
            tar.close()

        except Exception as e:
            print "failed to symlink:"+src
            print e 
            requests.post(progress_url, json={"status": "failed", "msg": str(e)})

#untar .tar.gz to local directory
#This is not necessary an import functionality, and maintly exists for scott's backup tool 
if "untar" in config:
    for file in config["untar"]:
        opcount += 1

        src = file["src"]
        dest = file["dest"]
        print "Handling untar request from",src,"to",dest

        progress_url = os.environ["SCA_PROGRESS_URL"]+".untar"+str(len(products));
        requests.post(progress_url, json={"status": "running", "progress": 0, "name": "un-tarring "+src+" to "+dest});
        try:

            taropt = ""
            if "opts" in file:
                taropt = file["opts"]

            #TODO - how should I handle existing directory?
            #TODO - extractall is *probably* slow - guessing from tarfile..
            #TODO - report progress report

            #now create tar file
            tar = tarfile.open(src, "r:"+taropt)
            tar.extractall(dest)

            requests.post(progress_url, json={"progress": 1, "status": "finished"});
            products.append({"filename": dest})
            tar.close()

        except Exception as e:
            print "failed to symlink:"+src
            print e 
            requests.post(progress_url, json={"status": "failed", "msg": str(e)})

with open("products.json", "w") as fp:
    json.dump([{"type": "raw", "files":products}], fp)

if opcount != len(products):
    print >> sys.stderr, "Not all request successfully processed."
    sys.exit(1) 

print "All request completed successfully"

