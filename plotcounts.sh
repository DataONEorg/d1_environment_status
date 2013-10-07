#!/bin/bash
# Simple shell script to download package counts from DataONE and then use R
# to plot them
# Author: Matt Jones, NCEAS, UC Santa Barbara

CURL="curl -g -k -s"
XML=xml
DFILE="plotcounts.csv"
#NDAYS=300
DSTART="2012-06-10"
#CMD="(( $(date "+%s") - $(date -j -f "%Y-%m-%d" ${DSTART} "+%s") ))/(60*60*24)"
#echo $CMD
NDAYS=$(echo "(( $(date "+%s") - $(date -j -f "%Y-%m-%d" ${DSTART} "+%s") ))/(60*60*24)" | bc)

function main {
    buildDataFile
    generatePlot
}

# Iterate over NDAYS days and get a package count for each day
function buildDataFile {
    echo "day | count" > $DFILE
    for (( d=0; d<=$NDAYS; d++ )); do 
        D=$(expr $NDAYS - $d)
        ((d = d + 4))
        count $D
    done
}

function generatePlot {
    R --no-save < plotcounts.R
}

# Function to retrieve a count of science metadata on the CNs up to a given date
function count {
    DAY=$1
    DATE=$(date -v "-${DAY}d" +%Y-%m-%d)
    TIME="T23:59:59.999Z/DAY%2B1DAYS"
    DM="*%20TO%20NOW-${DAY}DAY"
    MOD="dateModified:[${DM}]"
    #FORM="%20AND%20NOT%20formatId:%22http://www.openarchives.org/ore/terms%22"
    FORM="%20AND%20NOT%20formatType:RESOURCE"
    #FORM=""
    ROW="&rows=0"
    BASE="https://cn.dataone.org/cn/v1/search/solr?q="
    URI=${BASE}${MOD}${FORM}${ROW}
    echo ${URI}
    
    CNT=`$CURL ${URI} | $XML sel -N d1=http://ns.dataone.org/service/types/v1 -t -v /d1:objectList/@total`
    echo "$DATE, $CNT"
    echo "$DATE | $CNT" >> $DFILE
}
# execute the main method
main
