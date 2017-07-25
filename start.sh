#!/bin/bash

#need to reset the LANG to avoid following error from tarfile
#'ascii' codec can't decode byte 0xc3 in position 1: ordinal not in range(128)
#I tried setting environ["LANG"] and tarfile.ENCODING inside main.py, but that didn't fix it
export LANG="en_US.UTF-8"

if [ -z $SERVICE_DIR ]; then export SERVICE_DIR=`pwd`; fi
if [ -z $PROGRESS_URL ]; then export PROGRESS_URL="https://soichi7.ppa.iu.edu/api/progress/status/_sca.test"; fi

rm -f finished
rm -f pid

#do bigred2 specific things
#TODO - use ENV: HPC=BIGRED2 instead
echo $HOME | grep -i bigred > /dev/null
if [ $? -eq 0 ]; then
    module load python
fi

echo "starting main.py"
nohup python -u $SERVICE_DIR/main.py > stdout.log 2> stderr.log || echo $? > finished & 
echo $! > pid

