#!/bin/env python

import os
import json
import urllib2
import requests
import time

block_sz = 8192*10

with open('config.json') as config_json:
    config = json.load(config_json)

products = []

idx=0
for file in config["download"]:

    dir=file["dir"]
    if not os.path.exists(dir):
        os.makedirs(dir)

    url = file["url"]
    progress_url = os.environ["SCA_PROGRESS_URL"]+".file"+str(idx);
    requests.post(progress_url, json={"status": "running", "progress": 0, "name": url});
    try:
        u = urllib2.urlopen(url)
        file_name = url.split('/')[-1]
        f = open(dir+"/"+file_name, 'w')
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
                #print time.time()
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

            #status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
            #status = status + chr(8)*(len(status)+1) #what is this?
            #print status

        requests.post(progress_url, json={"progress": 1, "status": "finished"});
        products.append({"filename": file_name, "size": file_size_dl})

        f.close()
    #except urllib2.HTTPError, e:
    except Exception as e:
        print "failed to download "+url
        print e 
        requests.post(progress_url, json={"status": "failed", "msg": str(e)})

    idx+=1

with open("products.json", "w") as fp:
    json.dump(products, fp)

    #filesize=`curl -sI $url | grep Content-Length | cut -f 2 -d " "`
#
#echo "filesize: $filesize"
#echo "downloding $url"
#(cd download && curl -O $url)
#
##echo '[{"filename":"download/10142_3_MPRAGE_online.nii", "size":' $filesize '}]' > products.json
