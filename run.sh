#!/bin/bash

mkdir -p download

# to obtain the remote file size..

url="https://dl.dropboxusercontent.com/u/3209692/10142_3_MPRAGE_online.nii"
filesize=`curl -sI $url | grep Content-Length | cut -f 2 -d " "`
echo "filesize: $filesize"
echo "downloding $url"
(cd download && curl -O $url)

echo [{\"filename\":\"download/10142_3_MPRAGE_online.nii\", \"size\":\"$filesize\"}] > products.json
