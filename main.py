#!/usr/bin/env python
import os
import json
import urllib2
import requests
import time
import errno
import sys
import shutil
import subprocess
import cgi

block_sz = 8192*10

#didn't cure the problem..
#os.environ["LANG"] = "en_US.UTF-8"
#need to set it to UTF_8 to prevent
#'ascii' codec can't decode byte 0xc3 in position 1: ordinal not in range(128)
#tarfile.ENCODING="UTF-8"

with open('config.json') as config_json:
    config = json.load(config_json)

opcount = 0 #number of requested operations
products = []

def append_opt(taropt, cmd):
    if taropt == "gz":
        cmd.append("--gzip")
    if taropt == "bz2":
        cmd.append("--bzip2")
    if taropt  == "xz":
        cmd.append("--xz")

#download remote file via urllib2
if "download" in config:
    for file in config["download"]:
        opcount += 1

        #TODO - should I default it to "."?
        dir=file["dir"]
        if not os.path.exists(dir):
            os.makedirs(dir)

        url = file["url"]
        progress_url = os.environ["SCA_PROGRESS_URL"]+".file"+str(len(products));
        requests.post(progress_url, json={"status": "running", "progress": 0, "name": url});
        try:
            u = urllib2.urlopen(url)
            meta = u.info()

            if "untar" in file:
                products.append({"dirname": dir})

                print "untar requested for download"
                cmd = ["tar", "-x"]
                append_opt(file["untar"], cmd)
                cmd.append("--directory="+file["dir"])

                print cmd
                untar = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                f = untar.stdin
            else:
                #use filename specified via content-disposition or guess it from the url
                file_name = url.split('/')[-1]
                disphead = meta.getheaders("Content-Disposition")
                print disphead
                if disphead: 
                    value, params = cgi.parse_header(disphead[0])
                    file_name = params["filename"]

                #open file to output directly
                f = open(dir+'/'+file_name, 'w')
                products.append({"filename": dir+"/"+file_name, "size": file_size_dl})

            contentlength = meta.getheaders("Content-Length")
            if len(contentlength) == 1:
                file_size = int(meta.getheaders("Content-Length")[0])
            else:
                file_size = None
                print "Content-Length not set.. can't figure out the final file size"
                print meta

            print "Downloading: %s Bytes: %s" % (url, file_size)

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
            f.close()

        except Exception as e:
            print "failed to download "+url
            print e 
            requests.post(progress_url, json={"status": "failed", "msg": str(e)})

#(experimental)
#symlink files from local directory to task directory (dest is optional)
#TODO - due to the way symlink works, unlike copy, src needs to be relative to dest.. I need to 
#somehow make the src relative to the dest path (not taskdir)
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

            #make sure dest dir exists
            dirname = os.path.dirname(dest)
            if len(dirname) > 0:
                if not os.path.isdir(dirname):
                    print "making sure dir:",dirname,"exists"
                    os.makedirs(dirname)            

            try:
		src = os.path.abspath(src)
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

if "copy" in config:
    for file in config["copy"]:
        opcount += 1

        print "Handling copy request",file["src"]
        src = file["src"]

        progress_url = os.environ["SCA_PROGRESS_URL"]+".copy"+str(len(products));
        requests.post(progress_url, json={"status": "running", "progress": 0, "name": src});
        try:
            dest = src.split('/')[-1]
            if "dest" in file:
                dest = file["dest"]

            #make sure dest dir exists
            dirname = os.path.dirname(dest)
            if len(dirname) > 0:
                if not os.path.isdir(dirname):
                    print "making sure dir:",dirname,"exists"
                    os.makedirs(dirname)            

            shutil.copyfile(src, dest)
            requests.post(progress_url, json={"progress": 1, "status": "finished"});
            products.append({"filename": dest})

        except Exception as e:
            print "failed to copy:"+src
            print e 
            requests.post(progress_url, json={"status": "failed", "msg": str(e)})


#create tar file from local directory 
if "tar" in config:
    for file in config["tar"]:
        opcount += 1

        src = file["src"]
        dest = file["dest"]
        print "Handling tar request from",src,"to",dest

        progress_url = os.environ["SCA_PROGRESS_URL"]+".tar"+str(len(products));
        requests.post(progress_url, json={"status": "running", "progress": 0, "name": "tarring "+src+" to "+dest});
        try:

            #taropt can be "gz" or "bz2"..
            cmd = ["tar", "-c"]
            if "opts" in file:
                append_opt(file["opts"], cmd)

            cmd.append("--directory="+os.path.dirname(src))
            cmd.append("--file="+dest)
            cmd.append(os.path.basename(src))
            print cmd

            #TODO python tarfile is slow - maybe I should just drop to shell to run tar -cf..
            #now create tar file
            retcode = subprocess.call(cmd)
            if retcode == 0: 
                requests.post(progress_url, json={"progress": 1, "status": "finished"});
                products.append({"filename": dest})
            else:
                requests.post(progress_url, json={"status": "failed"});
                 
        except Exception as e:
            print "failed to tar:"+src
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

        #make sure dest dir exists
        if not os.path.isdir(dest):
            print "creating dest dir:",dest
            os.makedirs(dest)            

        progress_url = os.environ["SCA_PROGRESS_URL"]+".untar"+str(len(products));
        requests.post(progress_url, json={"status": "running", "progress": 0, "name": "un-tarring "+src+" to "+dest});
        try:

            cmd = ["tar", "-x"]
            if "opts" in file:
                append_opt(file["opts"], cmd)

            cmd.append("--directory="+dest)
            cmd.append("--file="+src)

            #print cmd
            retcode = subprocess.call(cmd)
            if retcode == 0: 
                requests.post(progress_url, json={"progress": 1, "status": "finished"});
                #TODO - dest only points to where we are unarchiving. 
                #I should add the base directory name inside the ardhive?
                products.append({"filename": dest})
            else:
                requests.post(progress_url, json={"status": "failed"});

        except Exception as e:
            print "failed to untar:"+src
            print e 
            requests.post(progress_url, json={"status": "failed", "msg": str(e)})

with open("products.json", "w") as fp:
    json.dump([{"type": "raw", "files":products}], fp)

if opcount != len(products):
    print >> sys.stderr, "Not all request successfully processed."
    sys.exit(1) 

print "All request completed successfully"

