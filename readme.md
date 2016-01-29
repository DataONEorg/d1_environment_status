# README for d1_environment_status

A collection of scripts for tracking the general state of a DataONE environment.


Contains a copy of the scripts and tools used to run the _production_history page on monitor.dataone.org.

Folders:

```
bin                  ~/bin
plotcounts           ~/.dataone/plotcounts
production_history   ~/sync/production_history
```

Crontab File:

```
# m h  dom mon dow   command
#0 */3 * * * /home/vieglais/bin/speedcheck.sh
03 5 * * * /home/vieglais/bin/get_production_info.sh
17 5 * * 5 /usr/bin/python /home/vieglais/bin/objectcounts.py --detail >> /dev/null
17 5 * * 0,1,2,3,4,6 /usr/bin/python /home/vieglais/bin/objectcounts.py >> /dev/null
23 5 * * * /usr/bin/python /home/vieglais/.dataone/plotcounts/src/get_state.py -l 2 --logsummary >> /home/vieglais/sync/production_history/data/production_log_history.csv
07 5 * * * /usr/bin/python /home/vieglais/.dataone/plotcounts/src/get_state.py >> /dev/null
#15 5 * * * /home/vieglais/bin/get_production_pids.sh
6 * * * * /home/vieglais/logcounts/getlogcounts.sh
#*/30 * * * * /home/vieglais/dataone_reindex_20151204/index_count.sh  >> /home/vieglais/dataone_reindex_20151204/totals.tsv
```

