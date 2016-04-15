# sca-service-curl
Curl downloader service for SCA.

It simply downloads files listed in the config.json via curl and create products.json for files successfully downloaded

* Installation

You probably need to install "pip install request"

* Input 

config.json
```
{
    "download: [
        {"url": "http://example.com/some/file.txt"},
        {"url": "http://example.com/another/file.txt"},
    ]
}
```

Upon execution, files will be downloaded under ./download

TODO..  Report to progress service for each file downloaded (use filesize?)
