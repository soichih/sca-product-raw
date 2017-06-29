#!/bin/bash

#need to reset the LANG to avoid following error from tarfile
#'ascii' codec can't decode byte 0xc3 in position 1: ordinal not in range(128)
#I tried setting environ["LANG"] and tarfile.ENCODING inside main.py, but that didn't fix it
export LANG="en_US.UTF-8"

#allows test execution
#if [ -z $SCA_WORKFLOW_DIR ]; then export SCA_WORKFLOW_DIR=`pwd`; fi
#if [ -z $SCA_TASK_DIR ]; then export SCA_TASK_DIR=`pwd`; fi
if [ -z $SERVICE_DIR ]; then export SERVICE_DIR=`pwd`; fi
if [ -z $PROGRESS_URL ]; then export PROGRESS_URL="https://soichi7.ppa.iu.edu/api/progress/status/_sca.test"; fi

#do bigred2 specific things
echo $HOME | grep -i bigred > /dev/null
if [ $? -eq 0 ]; then
    module load python
fi

rm -f finished
echo "starting main.py"
(
nohup time $SERVICE_DIR/main.py > stdout.log 2> stderr.log 
echo $? > finished 
) &

