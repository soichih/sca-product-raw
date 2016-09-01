#!/bin/bash

#need to reset the LANG to avoid following error from tarfile
#'ascii' codec can't decode byte 0xc3 in position 1: ordinal not in range(128)
#I tried setting environ["LANG"] and tarfile.ENCODING inside import.py, but that didn't fix it
export LANG="en_US.UTF-8"

#do bigred2 specific things
echo $HOME | grep -i bigred > /dev/null
if [ $? -eq 0 ]; then
    module load python
fi

rm -f finished
echo "starting import.py"
(
nohup time $SCA_SERVICE_DIR/import.py > stdout.log 2> stderr.log 
echo $? > finished 
) &

