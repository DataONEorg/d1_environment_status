## 2016-01-29

Migrated from subversion and merged with local edits from monitor.

Folders:

```
Local                Origin
bin                  ~/bin
plotcounts           ~/.dataone/plotcounts
production_history   ~/sync/production_history
```

Crontab File on monitor:

```
# m h  dom mon dow   command
#0 */3 * * * /home/vieglais/bin/speedcheck.sh
03 5 * * * /home/vieglais/bin/get_production_info.sh
17 5 * * 5 /usr/bin/python /home/vieglais/bin/objectcounts.py --detail >> /dev/null
17 5 * * 0,1,2,3,4,6 /usr/bin/python /home/vieglais/bin/objectcounts.py >> /dev/null
23 5 * * * /usr/bin/python /home/vieglais/.dataone/plotcounts/src/get_state.py -l 2 --logsummary >> /home/vieglais/sync/production_history/data/production_log_history.csv
07 5 * * * /usr/bin/python /home/vieglais/.dataone/plotcounts/src/get_state.py >> /dev/null
6 * * * * /home/vieglais/logcounts/getlogcounts.sh
```

