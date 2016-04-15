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
    u = urllib2.urlopen(url)
    file_name = url.split('/')[-1]
    f = open(dir+"/"+file_name, 'w')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])

    progress_url = os.environ["SCA_PROGRESS_URL"]+".file"+str(idx);
    requests.post(progress_url, json={"status": "running", "progress": 0, "msg": "downloading "+url+" ("+str(file_size)+" bytes)"});

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
            requests.post(progress_url, json={"progress": float(file_size_dl)/file_size})
            progress_time = time.time()
            status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
            print status

        #status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        #status = status + chr(8)*(len(status)+1) #what is this?
        #print status

    requests.post(progress_url, json={"progress": 1, "status": "finished"});
    products.append({"filename": file_name, "size": file_size})

    f.close()
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
