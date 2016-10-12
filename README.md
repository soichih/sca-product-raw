
SCA raw data type 

## main.py

If executed as SCA service, this service will download files listed and create products.json for files successfully downloaded. Download progress will be posted to SCA_PROGRESS_URL

* Installation

You probably need to install "pip install request"

* Input 

config.json

```
{
    "download": [
        {"dir": "download", "url": "https://dl.dropboxusercontent.com/u/3209692/permanent/10142_3_MPRAGE_online.nii"},
        {"dir": "download", "url": "http://broken_url.com"}
    ],
    "symlink": [
        {"src": "/etc/issue"},
        {"src": "/etc/fstab", "dest": "fstab.lnk"}
    ]
}
```

Sample products.json

```
[
    {
        "files": [
            {"size": 21627232, "filename": "download/10142_3_MPRAGE_online.nii"}, 
            {"filename": "issue"}, 
            {"filename": "fstab.lnk"}
        ], 
        "type": "raw"
    }
]
```

## UI

/ui provides angular directive to easily show content of the taskdir using SCA API. Apart from the usual SCA configuration,
you will need following angular dependencies 

> https://github.com/yaru22/angular-timeago
