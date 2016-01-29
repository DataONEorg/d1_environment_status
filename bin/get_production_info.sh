#!/bin/sh

BASEURL="https://cn.dataone.org/cn/v1"
DESTDIR=/home/vieglais/sync/production_history/history
DEST=${DESTDIR}/$(date +"%Y%m%d")

/usr/bin/curl -s "${BASEURL}/node" > ${DEST}_nodes.xml
/usr/bin/curl -s "${BASEURL}/formats" > ${DEST}_formats.xml


