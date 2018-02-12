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

print "Starting service"

block_sz = 16*1024

with open('config.json') as config_json:
    config = json.load(config_json)

opcount = 0 #number of requested operations
success = 0 #number of request successfully fulfilled

def ext2taropt(ext, cmd):
    if ext == "tar":
        None
    if ext == "gz":
        cmd.append("--gzip")
    if ext == "bz2":
        cmd.append("--bzip2")
    if ext == "xz":
        cmd.append("--xz")

#download remote file via urllib2
if "download" in config:
    for file in config["download"]:
        opcount += 1

        url = file["url"]
        #print "downloading", url #TODO- truncate the at=.....
        print "downloading", file["dir"]

        #shorten url if we could.. some url contains token..
	url_to_show = url
        try: 
            url_qpos = url.index("?")
            if url_qpos > 0:
                url_to_show=url[0:url_qpos]
        except ValueError:
            None

        #TODO - should I default it to "."?
        #TODO - I think I should restrict dir to be under current directory
        dir=file["dir"]
        if not os.path.exists(dir):
            os.makedirs(dir)

        if "PROGRESS_URL" in os.environ:
            progress_url = os.environ["PROGRESS_URL"]+".file"+str(success);
            requests.post(progress_url, json={"status": "running", "progress": 0, "name": url});

        try:
            u = urllib2.urlopen(url)
            meta = u.info()

            #use filename specified via content-disposition or guess it from the url
            file_name = url.split('/')[-1]
            disphead = meta.getheaders("Content-Disposition")
            if disphead: 
                value, params = cgi.parse_header(disphead[0])
                file_name = params["filename"]

            contentlength = meta.getheaders("Content-Length")
            if len(contentlength) == 1:
                file_size = int(meta.getheaders("Content-Length")[0])
            else:
                file_size = None
                print "Content-Length not set.. can't figure out the final file size"
                print meta

            #create writestream 
            if "untar" in file:
                #print "Un-tarring", file["untar"]
                cmd = ["tar", "-v", "-x"]

                #guess which extraction option to use for tar
                ext = file["untar"]
                if ext == "auto":
                    ext = os.path.splitext(file_name)[1][1:]
                ext2taropt(ext, cmd)

                cmd.append("--directory="+dir)

                untar = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=sys.stderr)
                writestream = untar.stdin
            else:
                print "Using",dir+"/"+file_name
                writestream = open(dir+'/'+file_name, 'w')

            #commencing download 
            file_size_dl = 0
            progress_time = time.time()
            while True:
                buffer = u.read(block_sz)
                if not buffer:
                    break

                file_size_dl += len(buffer)
                writestream.write(buffer)

                #report progress
                if time.time() - progress_time > 0.5:
                    if "PROGRESS_URL" in os.environ:
                        if file_size:
                            requests.post(progress_url, json={"progress": float(file_size_dl)/file_size})
                        else:
                            requests.post(progress_url, json={"msg": "Downloaded "+str(file_size_dl)+ " -- total size unknown"})

                    progress_time = time.time()
                    if file_size:
                        status = r"%10d bytes [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
                    else:
                        status = r"%10d bytes" % (file_size_dl)
		    print "Downloading %s (%s)" % (file_name, status)

            if u.getcode() == 200:

                #check tar return code
                try:
                    writestream.wait()
                    code = writestream.returncode
                except:
                    writestream.close()
                    code = 0
                if code != 0:
                    raise Exception("writestream ended with "+code)

                if file_size and file_size != file_size_dl:
                    raise Exception("Couldn't download the whole file.")

                if "PROGRESS_URL" in os.environ:
                    requests.post(progress_url, json={"progress": 1, "status": "finished"});

                print "Successfully downloaded"
                success += 1
            else:
                print "Download failed with code %d" % (u.getcode())
                if "PROGRESS_URL" in os.environ:
                    requests.post(progress_url, json={"status": "failed", "msg": "non-200"})

        except Exception as e:
            print "failed to download "+url
            print e 
            if "PROGRESS_URL" in os.environ:
                requests.post(progress_url, json={"status": "failed", "msg": str(e)})

#(experimental)
#symlink files from local directory to task directory (dest is optional)
#TODO - due to the way symlink works, unlike copy, src needs to be relative to dest.. I need to 
#somehow make the src relative to the dest path (not taskdir)
if "symlink" in config:
    for file in config["symlink"]:
        opcount += 1

        print "Handling symlink request",file
        src = file["src"]

        if "PROGRESS_URL" in os.environ:
            progress_url = os.environ["PROGRESS_URL"]+".symlink"+str(success);
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
                if "PROGRESS_URL" in os.environ:
                    requests.post(progress_url, json={"progress": 1, "status": "finished"});
                #products.append({"filename": dest})
                success+=1
            except OSError, e:
                if e.errno == errno.EEXIST:
                    os.remove(dest)
                    os.symlink(src, dest)
                    if "PROGRESS_URL" in os.environ:
                        requests.post(progress_url, json={"progress": 1, "status": "finished"});
                    #products.append({"filename": dest})
                    success+=1

        except Exception as e:
            print "failed to symlink:"+src
            print e 
            if "PROGRESS_URL" in os.environ:
                requests.post(progress_url, json={"status": "failed", "msg": str(e)})

if "copy" in config:
    for file in config["copy"]:
        opcount += 1

        print "Handling copy request",file
        src = file["src"]

        if "PROGRESS_URL" in os.environ:
            progress_url = os.environ["PROGRESS_URL"]+".copy"+str(success);
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
            if "PROGRESS_URL" in os.environ:
                requests.post(progress_url, json={"progress": 1, "status": "finished"});
            #products.append({"filename": dest})
            success += 1

        except Exception as e:
            print "failed to copy:"+src
            print e 
            if "PROGRESS_URL" in os.environ:
                requests.post(progress_url, json={"status": "failed", "msg": str(e)})

#create tar file from local directory 
if "tar" in config:
    for file in config["tar"]:
        opcount += 1

        src = file["src"]
        dest = file["dest"]
        print "Handling tar request",file

        if "PROGRESS_URL" in os.environ:
            progress_url = os.environ["PROGRESS_URL"]+".tar"+str(success);
            requests.post(progress_url, json={"status": "running", "progress": 0, "name": "tarring "+src+" to "+dest});
        try:

            #taropt can be "gz" or "bz2"..
            cmd = ["tar", "-c"]
            if "opts" in file:

                ext = file["opts"]
                if ext == "auto":
                    ext = os.path.splitext(dest)[1][1:]
                    #print "auto-detecting dest tar ext",dest, ext

                ext2taropt(ext, cmd)

            #TODO - passing "dir" to dirname() will result in empty string??
            cmd.append("--directory="+os.path.dirname(src))
            cmd.append("--file="+dest)
            cmd.append(os.path.basename(src))
            #print cmd

            #now create tar file
            retcode = subprocess.call(cmd)
            if retcode == 0: 
                #products.append({"filename": dest})
                success+=1
                if "PROGRESS_URL" in os.environ:
                    requests.post(progress_url, json={"progress": 1, "status": "finished"});
            else:
                if "PROGRESS_URL" in os.environ:
                    requests.post(progress_url, json={"status": "failed"});
                 
        except Exception as e:
            print "failed to tar:"+src
            print e 
            if "PROGRESS_URL" in os.environ:
                requests.post(progress_url, json={"status": "failed", "msg": str(e)})

#untar .tar.gz to local directory
#This is not necessary an import functionality, and maintly exists for scott's backup tool 
#TODO - maybe I should deprecate this?
if "untar" in config:
    for file in config["untar"]:
        opcount += 1

        src = file["src"]
        dest = file["dest"]
        print "Handling untar", file

        #src/dest sent to Popen cmd array.. validate? (I think popen makes sure that each token are string, but paths themselves should be under workdir?)

        #make sure dest dir exists
        if not os.path.isdir(dest):
            print "creating dest dir:",dest
            os.makedirs(dest)            

        if "PROGRESS_URL" in os.environ:
            progress_url = os.environ["PROGRESS_URL"]+".untar"+str(success);
            requests.post(progress_url, json={"status": "running", "progress": 0, "name": "un-tarring "+src+" to "+dest});
        try:
            cmd = ["tar", "-v", "-x"]
            if "opts" in file:

                ext = file["opts"]
                if ext == "auto":
                    ext = os.path.splitext(src)[1][1:]
                    #print "auto-detecting untar ext",src, ext

                ext2taropt(ext, cmd)

            cmd.append("--directory="+dest)
            cmd.append("--file="+src)

            #print cmd
            retcode = subprocess.call(cmd)
            if retcode == 0: 
                if "PROGRESS_URL" in os.environ:
                    requests.post(progress_url, json={"progress": 1, "status": "finished"});

                #TODO - dest only points to where we are unarchiving. 
                #I should add the base directory name inside the ardhive?
                #products.append({"filename": dest})
                success+=1
            else:
                if "PROGRESS_URL" in os.environ:
                    requests.post(progress_url, json={"status": "failed"});

        except Exception as e:
            print "failed to untar:"+src
            print e 
            if "PROGRESS_URL" in os.environ:
                requests.post(progress_url, json={"status": "failed", "msg": str(e)})

#with open("product.json", "w") as fp:
#    json.dump({"type": "raw", "files":products}, fp)

#write finished (can't nohup catch this?)
f = open('finished', 'w')
if opcount != success:
    print "Not all request successfully processed."
    f.write('1')
else:
    print "All request completed successfully."
    f.write('0')
f.close()


