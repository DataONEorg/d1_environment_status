#!/bin/bash

URL="https://cn.dataone.org/cn/v1/query/logsolr/?q=*:*"
URL2="https://cn-orc-1.dataone.org/cn/v1/query/logsolr/?q=*:*"
FOLDER="/home/vieglais/sync/production_history/log_info_tmp"
FN="${FOLDER}/totals.txt"
FN2="${FOLDER}/totals-orc.txt"
XML="/usr/local/bin/xml"

tnow=$(date +'%Y%m%dT%H%M%S')
nrecs=$(curl -s ${URL} | ${XML} sel -t -m "//result" -v "@numFound")
echo "${tnow}, ${nrecs}" >> ${FN}

nrecs=$(curl -s ${URL2} | ${XML} sel -t -m "//result" -v "@numFound")
echo "${tnow}, ${nrecs}" >> ${FN2}
