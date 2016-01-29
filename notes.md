# Notes 

Notes on changes and operation.


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


To refresh the *entire* log history csv file:

```
python ~/.dataone/plotcounts/src/get_state.py -l 2 -D ALL --logsummary \
 > ${HOME}/sync/production_history/data/production_log_history.csv
```

Error codes reported by socket error:

```
-1001 : EPERM
-1002 : ENOENT
-1003 : ESRCH
-1004 : EINTR
-1005 : EIO
-1006 : ENXIO
-1007 : E2BIG
-1008 : ENOEXEC
-1009 : EBADF
-1010 : ECHILD
-1011 : EDEADLK
-1012 : ENOMEM
-1013 : EACCES
-1014 : EFAULT
-1015 : ENOTBLK
-1016 : EBUSY
-1017 : EEXIST
-1018 : EXDEV
-1019 : ENODEV
-1020 : ENOTDIR
-1021 : EISDIR
-1022 : EINVAL
-1023 : ENFILE
-1024 : EMFILE
-1025 : ENOTTY
-1026 : ETXTBSY
-1027 : EFBIG
-1028 : ENOSPC
-1029 : ESPIPE
-1030 : EROFS
-1031 : EMLINK
-1032 : EPIPE
-1033 : EDOM
-1034 : ERANGE
-1035 : EAGAIN
-1036 : EINPROGRESS
-1037 : EALREADY
-1038 : ENOTSOCK
-1039 : EDESTADDRREQ
-1040 : EMSGSIZE
-1041 : EPROTOTYPE
-1042 : ENOPROTOOPT
-1043 : EPROTONOSUPPORT
-1044 : ESOCKTNOSUPPORT
-1045 : ENOTSUP
-1046 : EPFNOSUPPORT
-1047 : EAFNOSUPPORT
-1048 : EADDRINUSE
-1049 : EADDRNOTAVAIL
-1050 : ENETDOWN
-1051 : ENETUNREACH
-1052 : ENETRESET
-1053 : ECONNABORTED
-1054 : ECONNRESET
-1055 : ENOBUFS
-1056 : EISCONN
-1057 : ENOTCONN
-1058 : ESHUTDOWN
-1059 : ETOOMANYREFS
-1060 : ETIMEDOUT
-1061 : ECONNREFUSED
-1062 : ELOOP
-1063 : ENAMETOOLONG
-1064 : EHOSTDOWN
-1065 : EHOSTUNREACH
-1066 : ENOTEMPTY
-1067 : EPROCLIM
-1068 : EUSERS
-1069 : EDQUOT
-1070 : ESTALE
-1071 : EREMOTE
-1072 : EBADRPC
-1073 : ERPCMISMATCH
-1074 : EPROGUNAVAIL
-1075 : EPROGMISMATCH
-1076 : EPROCUNAVAIL
-1077 : ENOLCK
-1078 : ENOSYS
-1079 : EFTYPE
-1080 : EAUTH
-1081 : ENEEDAUTH
-1082 : EPWROFF
-1083 : EDEVERR
-1084 : EOVERFLOW
-1085 : EBADEXEC
-1086 : EBADARCH
-1087 : ESHLIBVERS
-1088 : EBADMACHO
-1089 : ECANCELED
-1090 : EIDRM
-1091 : ENOMSG
-1092 : EILSEQ
-1093 : ENOATTR
-1094 : EBADMSG
-1095 : EMULTIHOP
-1096 : ENODATA
-1097 : ENOLINK
-1098 : ENOSR
-1099 : ENOSTR
-1100 : EPROTO
-1101 : ETIME
-1102 : EOPNOTSUPP
-1103 : ENOPOLICY
-1104 : ENOTRECOVERABLE
-1105 : EOWNERDEAD
```
