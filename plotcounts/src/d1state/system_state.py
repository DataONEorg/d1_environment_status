'''
Created on Feb 27, 2014

@author: vieglais

Generates a JSON object that provides a high level description of the state of
a DataONE environment at the time.

The resulting JSON can be processed with Javascript and HTML to provide a 
state view, or can be loaded back into the Python structure for additional 
processing.
'''

import logging
import pprint
import datetime
import json
import socket
import httplib
import math
import dns.resolver
import d1_common.types.exceptions
from d1_client import cnclient, cnclient_1_1
from d1_client import mnclient


def getNow(asDate=False):
  ctime = datetime.datetime.utcnow()
  return ctime


def getNowString(ctime=None):
  if ctime is None:
    ctime = getNow()
  return ctime.strftime("%Y-%m-%d %H:%M:%S.0+00:00")


def dateTimeToListObjectsTime(dt):
  '''Return a string representation of a datetime that can be used in toDate or 
  fromDate in a listObject API call.
  %Y-%m-%dT%H:%M:%S
  '''
  return dt.strftime("%Y-%m-%dT%H:%M:%S")


def dateTimeToSOLRTime(dt):
  '''Return a string representation of a datetime that can be used in SOLR
  queries against dates such as dateUploaded 
  fromDate in a listObject API call.
  '''
  return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
  

def escapeQueryTerm(term):
  '''
  + - && || ! ( ) { } [ ] ^ " ~ * ? : \
  '''
  reserved = ['+','-','&','|','!','(',')','{','}','[',']','^','"','~','*','?',':',]
  term = term.replace(u'\\',u'\\\\')
  for c in reserved:
    term = term.replace(c,u"\%s" % c)
  return term

class NodeState(object):
  
  def __init__(self, baseURL):
    self.log = logging.getLogger(str(self.__class__.__name__))
    self.baseurl = baseURL
    self.clientv1 = mnclient.MemberNodeClient( self.baseurl )

  
  def count(self):
    '''
    Return the number of objects on the node as reported by listObjects
    
Exceptions.NotAuthorized – (errorCode=401, detailCode=1520)
Exceptions.InvalidRequest – (errorCode=400, detailCode=1540)
Exceptions.NotImplemented –
(errorCode=501, detailCode=1560)
Raised if some functionality requested is not implemented. In the case of an optional request parameter not being supported, the errorCode should be 400. If the requested format (through HTTP Accept headers) is not supported, then the standard HTTP 406 error code should be returned.
Exceptions.ServiceFailure – (errorCode=500, detailCode=1580)
Exceptions.InvalidToken – (errorCode=401, detailCode=1530)    

exception httplib.HTTPException
exception httplib.NotConnected -10
exception httplib.InvalidURL -11
exception httplib.UnknownProtocol -12
exception httplib.UnknownTransferEncoding -13
exception httplib.UnimplementedFileMode -14
exception httplib.IncompleteRead -15
exception httplib.ImproperConnectionState -16
exception httplib.CannotSendRequest -17
exception httplib.CannotSendHeader -18
exception httplib.ResponseNotReady -19
exception httplib.BadStatusLine -20
    '''
    try:
      res = self.clientv1.listObjects(start=0, count=0)
      return res.total
    except d1_common.types.exceptions.NotAuthorized as e:
      self.log.error(e)
      return -401
    except d1_common.types.exceptions.InvalidRequest as e:
      self.log.error(e)
      return -400
    except d1_common.types.exceptions.NotImplemented as e:
      self.log.error(e)
      return -501
    except d1_common.types.exceptions.ServiceFailure as e:
      self.log.error(e)
      return -500
    except d1_common.types.exceptions.InvalidToken as e:
      self.log.error(e)
      return -401
    except httplib.NotConnected as e:
      self.log.error(e)
      return -10
    except httplib.InvalidURL as e:
      self.log.error(e)
      return -11
    except httplib.UnknownProtocol as e:
      self.log.error(e)
      return -12
    except httplib.UnknownTransferEncoding as e:
      self.log.error(e)
      return -13
    except httplib.UnimplementedFileMode as e:
      self.log.error(e)
      return -14
    except httplib.IncompleteRead as e:
      self.log.error(e)
      return -15
    except httplib.ImproperConnectionState as e:
      self.log.error(e)
      return -16
    except httplib.CannotSendRequest as e:
      self.log.error(e)
      return -17
    except httplib.CannotSendHeader as e:
      self.log.error(e)
      return -18
    except httplib.ResponseNotReady as e:
      self.log.error(e)
      return -19
    except httplib.BadStatusLine as e:
      self.log.error(e)
      return -20
    except socket.error as e:
      self.log.error(e)
      #See notes.md for a list of error codes
      if hasattr(e, 'errno'):
        if e.errno is not None:
          return -1000 - e.errno
      return -21
       
    except Exception as e:
      '''Something else. Need to examine the client connection object
      '''     
      self.log.error("Error not trapped by standard exception.")
      self.log.error(e)
      return -1



class EnvironmentState(object):
  #increment the version flag if there's a change to the generated data structure  
  VERSION = "18"
  COUNT_PUBLIC = None
  COUNT_PUBLIC_CURRENT = "-obsoletedBy:[* TO *]"
  TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.0+00:00"
  JS_VARIABLE_STATE = "var env_state = "
  JS_VARIABLE_INDEX = "var env_state_index = "
  JS_VARIABLE_NODES = "var node_state_index = "
  #TODO: These IP addresses are specific to the production environment and 
  #include changes to UCSB and ORC
  CN_IP_ADDRESSES = ['160.36.134.71',
                     '128.111.220.46',
                     '128.111.54.80',
                     '128.111.36.80',
                     '160.36.13.150',
                     '64.106.40.6',
                     #'128.219.49.14', #This is a proxy server at ORNL
                     '128.111.220.51', #UCSB Nagios
                     '128.111.84.5', ] #UCSB Nagios

  LOG_EVENTS = [['create','Created using DataONE API'], 
                ['read', 'Content downloaded'], 
                ['read.ext', 'Content downloaded by entities other than CNs'], 
                ['update', 'Updated'], 
                ['delete', 'Deleted'], 
                ['replicate', 'Content retrieved by replication process'], 
                ['synchronization_failed', 'Attempt to synchronize failed'], 
                ['replication_failed', 'Attempt to replicate failed'],
               ]

  
  def __init__(self, baseurl, cert_path=None):
    self.log = logging.getLogger(str(self.__class__.__name__))
    self.log.debug("Initializing...")
    self.baseurl = baseurl
    self.state = {'meta':None,
                  'formats':None,
                  'nodes':None,
                  'counts':None,
                  'summary': None,
                  'dns': None,
                  'logs': None,
                  }
    self.clientv1 = cnclient.CoordinatingNodeClient( self.baseurl, 
                                                     cert_path=cert_path )
    self.clientv11 = cnclient_1_1.CoordinatingNodeClient( self.baseurl,
                                                          cert_path=cert_path )


  def __str__(self):
    return pprint.pformat( self.state )


  def populateState(self):
    '''Populates self.state with current environment status
    '''
    self.tstamp = getNow()
    meta = {'tstamp': getNowString(self.tstamp),
            'baseurl': self.baseurl,
            'version': EnvironmentState.VERSION,
            'count_meta': {0:'ALL',
                           1:EnvironmentState.COUNT_PUBLIC,
                           2:EnvironmentState.COUNT_PUBLIC_CURRENT}
            }
    self.state['meta'] = meta
    self.state['formats'] = self.getFormats()
    self.state['nodes'] = self.getNodes()
    self.state['dns'] = self.getDNSInfo()
    self.state['logs'] = self.getLogSummary()
    self.state['counts'] = self.getCounts()
    self.state['summary'] = self.summarizeCounts()
    self.state['summary']['sizes'] = self.getObjectTypeSizeHistogram()
    
    
  def retrieveLogResponse(self, q, fq=None):
    self.clientv1.connection.close()
    url = self.clientv1._rest_url('log')
    query = {'q': q}
    if not fq is None:
      query['fq'] = fq
    #logging.info("URL = %s" % url)
    response = self.clientv1.GET(url, query)
    logrecs = self.clientv1._read_dataone_type_response(response)
    return logrecs.total
    
    
  def getLogSummary(self):
    periods = [['Day', 'dateLogged:[NOW-1DAY TO NOW]', 'Past day'],
               ['Week', 'dateLogged:[NOW-7DAY TO NOW]', 'Past week'],
               ['Month', 'dateLogged:[NOW-1MONTH TO NOW]', 'Past month'],
               ['Year', 'dateLogged:[NOW-1YEAR TO NOW]', 'Past year'],
               ['All', 'dateLogged:[2012-07-01T00:00:00.000Z TO NOW]', 'Since July 1, 2012'],
              ]
    res = {'events': EnvironmentState.LOG_EVENTS,
           'periods': map(lambda p: [p[0], p[2]], periods),
           'data': {}}
    exclude_cns = "-ipAddress:({0})"\
                    .format( " OR ".join(EnvironmentState.CN_IP_ADDRESSES))
    for event in EnvironmentState.LOG_EVENTS:
      res['data'][event[0]] = {}
      for period in periods:
        self.log.info('Log for {0} over {1}'.format(event[0], period[0]))
        if event[0].endswith('.ext'):
          ev = event[0].split(".")[0]
          q = "event:{0} AND {1}".format(ev, exclude_cns)
        else:
          q = "event:{0}".format(event[0])
        fq = period[1]
        nrecords = self.retrieveLogResponse(q, fq=fq)
        res['data'][event[0]][period[0]] = nrecords
    return res

    
  def getDNSInfo(self):
    #TODO: Make this responsive to the CNode specified in the constructor
    res = {'cn-ucsb-1.dataone.org':{},
           'cn-unm-1.dataone.org':{},
           'cn-orc-1.dataone.org':{},
           'cn.dataone.org':{}
           }
    for k in res.keys():
      info = dns.resolver.query(k)
      res[k]['address'] = []
      for ip in info:
        res[k]['address'].append(ip.to_text())
    return res;


  def getCountsToDate(self, to_date, exclude_listObjects=False):
    self.tstamp = getNow()
    meta = {'tstamp': getNowString(self.tstamp),
            'baseurl': self.baseurl,
            'version': EnvironmentState.VERSION,
            'count_meta': {0:'ALL',
                           1:EnvironmentState.COUNT_PUBLIC,
                           2:EnvironmentState.COUNT_PUBLIC_CURRENT}
            }
    self.state['meta'] = meta
    self.state['formats'] = self.getFormats()
    self.state['counts'] = self.getCounts(as_of_date = to_date,
                                          exclude_listObjects=exclude_listObjects)
    self.state['summary'] = self.summarizeCounts()


  def getNodes(self):
    '''Returns a dictionary of node information, keyed by nodeId
    '''
    
    def syncschedule_array(s):
      if s is None:
        return {}
      # hour mday min mon sec wday year
      # year, mon, mday, wday, hour, min, sec
      return [s.year, s.mon, s.mday, s.wday, s.hour, s.min, s.sec]
    
    res = {}
    nodes = self.clientv1.listNodes()
    for node in nodes.node:
      entry = {'name' : node.name,
               'description' : node.description,
               'baseurl' : node.baseURL,
               'type' : node.type,
               'state': node.state,
               'objectcount': -1,
                }
      sync = node.synchronization
      if not sync is None:
        entry['sync.schedule'] = syncschedule_array(sync.schedule)
        entry['sync.lastHarvested'] = sync.lastHarvested.strftime("%Y-%m-%d %H:%M:%S.0%z")
        entry['sync.lastCompleteHarvest'] = sync.lastCompleteHarvest.strftime("%Y-%m-%d %H:%M:%S.0%z")
        #Call list objects to get a count
        self.log.info("Attempting node count on {0}".format(node.baseURL))
        ns = NodeState(node.baseURL)
        entry['objectcount'] = ns.count()
        
      res[node.identifier.value()] = entry
    return res


  def getFormats(self):
    res = {}
    formats = self.clientv1.listFormats()
    for format in formats.objectFormat:
      res[format.formatId] = {'name' : format.formatName,
                              'type' : format.formatType}
    return res


  def _countAll(self, counts, as_of_date=None):
    '''Returns object counts by formatId using listObjects
    Requires that self.state['formats'] has been populated
    '''
    to_date = None
    if not as_of_date is None:
      to_date = dateTimeToListObjectsTime(as_of_date)
    for formatId in self.state['formats'].keys():
      res = self.clientv11.listObjects(count=0, 
                                       formatId=formatId, 
                                       toDate=to_date)
      self.log.info("{0:s} : {1:d}".format(formatId, res.total))
      self.state['counts'][formatId][0] = res.total
    


  def _countSOLR(self, counts, col=1, fq=None, as_of_date=None):
    '''Populates counts 
    '''
    queryEngine = "solr"
    query='/'
    maxrecords = 0
    fields = 'id'    
    date_restriction = ''
    if not as_of_date is None:
      date_restriction = " AND dateUploaded:[* TO {0:s}]".format(dateTimeToSOLRTime(as_of_date))
    for formatId in self.state['formats'].keys():
      q = "formatId:\"{0:s}\"".format(escapeQueryTerm(formatId))
      q = q + date_restriction
      ntries = 0
      while ntries < 4:
        try:
          ntries += 1
          results = eval(self.clientv1.query(queryEngine, query=query, 
                                  q=q,
                                  fq=fq,
                                  wt='python', 
                                  fl=fields, 
                                  rows=maxrecords).read())
          break
        except httplib.BadStatusLine as e:
          self.log.warn(e)
          
      nHits = results['response']['numFound']
      self.state['counts'][formatId][col] = nHits
      self.log.info("{0:s} : {1:d}".format(formatId, nHits))


  def getCounts(self, as_of_date=None, exclude_listObjects=False):
    '''return object counts, optionally as of the specified date (datetime)
    '''
    #initialize the storage space
    counts = {}
    for formatId in self.state['formats'].keys():
      counts[formatId] = [0, 0, 0]
    self.state['counts'] = counts
    #populate the number of all objects
    for k in self.state['meta']['count_meta'].keys():
      if k == 0:
        if not exclude_listObjects:
          self._countAll(counts, as_of_date=as_of_date)
      else:
        self._countSOLR(counts, 
                        col=k, 
                        fq=self.state['meta']['count_meta'][k],
                        as_of_date=as_of_date)
    return counts


  def getObjectSizeHistogram(self, q="*:*", nbins=10):
    '''Returns a list of [size_low, size_high, count] for objects that match
    the specified query.
    To find minimum value: 
      https://cn.dataone.org/cn/v1/query/solr/?fl=size&sort=size%20asc&q=*:*&rows=1
    to find maximum value:
      https://cn.dataone.org/cn/v1/query/solr/?fl=size&sort=size%20desc&q=*:*&rows=1
    '''

    def getSOLRResponse(q, maxrecords, fields, rsort, fq=None):
      ntries = 0
      while ntries < 4:
        try:
          ntries += 1
          results = eval(self.clientv1.query("solr", query="/", 
                                  q=q,
                                  fq=fq,
                                  wt='python', 
                                  fl=fields, 
                                  sort=rsort,
                                  rows=maxrecords).read())
          return results
        except httplib.BadStatusLine as e:
          self.log.warn(e)
      return None
      
    minval = getSOLRResponse(q, 1, 'size', "size asc")['response']['docs'][0]['size']
    maxval = getSOLRResponse(q, 1, 'size', "size desc")['response']['docs'][0]['size']
    if minval <1:
      minval = 1
    lminval = math.log10(minval)
    lmaxval = math.log10(maxval)
    binsize = (lmaxval - lminval) / (nbins*1.0)
    res = []
    for i in xrange(0, nbins):
      row = [math.pow(10, lminval + i*binsize), 
             math.pow(10, lminval + (i+1)*binsize), 
             0]
      res.append(row)
    for i in xrange(0, nbins):
      row = res[i]
      if i == 0:
        fq = "size:[{0:d} TO {1:d}]".format(math.trunc(row[0]), math.trunc(row[1]))
      elif i == nbins-1:
        fq = "size:[{0:d} TO {1:d}]".format(math.trunc(row[0]), math.trunc(row[1])+1)
      else:
        fq = "size:[{0:d} TO {1:d}]".format(math.trunc(row[0])+1, math.trunc(row[1]))
      n = getSOLRResponse(q, 0, 'size', 'size asc', fq=fq)['response']['numFound']
      res[i][2] = n
    return {"minimum": minval,
            "maximum": maxval,
            "histogram": res}


  def getObjectTypeSizeHistogram(self):
    res = {'data':[],
           'metadata':[],
           'resource':[]}
    res['data'] = self.getObjectSizeHistogram(q="formatType:DATA")
    res['metadata'] = self.getObjectSizeHistogram(q="formatType:METADATA")
    res['resource'] = self.getObjectSizeHistogram(q="formatType:RESOURCE")
    return res


  def summarizeCounts(self):
    '''Computes summary totals for DATA, METADATA, and RESOURCE objects
    '''
    totalcols = ['data', 'meta', 'resource']
    summary = {'all': {'data':0, 'meta': 0, 'resource': 0, 'total': 0},
               'public': {'data':0, 'meta': 0, 'resource': 0, 'total': 0},
               'public_notobsolete': {'data':0, 'meta': 0, 'resource': 0, 'total': 0}
               }
    for fmt in self.state['formats'].keys():
      if self.state['formats'][fmt]['type'] == 'DATA':
        summary['all']['data'] = summary['all']['data'] + self.state['counts'][fmt][0]
        summary['public']['data'] = summary['public']['data'] + self.state['counts'][fmt][1]
        summary['public_notobsolete']['data'] = summary['public_notobsolete']['data'] + self.state['counts'][fmt][2]
      elif self.state['formats'][fmt]['type'] == 'METADATA':
        summary['all']['meta'] = summary['all']['meta'] + self.state['counts'][fmt][0]
        summary['public']['meta'] = summary['public']['meta'] + self.state['counts'][fmt][1]
        summary['public_notobsolete']['meta'] = summary['public_notobsolete']['meta'] + self.state['counts'][fmt][2]
      elif self.state['formats'][fmt]['type'] == 'RESOURCE':
        summary['all']['resource'] = summary['all']['resource'] + self.state['counts'][fmt][0]
        summary['public']['resource'] = summary['public']['resource'] + self.state['counts'][fmt][1]
        summary['public_notobsolete']['resource'] = summary['public_notobsolete']['resource'] + self.state['counts'][fmt][2]
    for ctype in summary.keys():
      summary[ctype]['total'] = summary[ctype]['data']
      summary[ctype]['total'] = summary[ctype]['total'] + summary[ctype]['meta']
      summary[ctype]['total'] = summary[ctype]['total'] + summary[ctype]['resource']
    self.state['summary'] = {'counts' : summary}
    return summary
    

  def asJSON(self, outStream):
    outStream.write(EnvironmentState.JS_VARIABLE_STATE)
    json.dump(self.state, outStream, indent=2)
  
  
  def fromJSON(self, inStream):
    jbuffer = inStream.read()
    self.state = json.loads(jbuffer[len(EnvironmentState.JS_VARIABLE_STATE):])
    self.tstamp = datetime.datetime().strptime(self.state['meta']['tstamp'],"%Y-%m-%d %H:%M:%S.0+00:00")
    
  
  def getTStamp(self):
    return self.state['meta']['tstamp']


#===============================================================================
def test1(baseurl="https://cn.dataone.org/cn"):
  es = EnvironmentState(baseurl)
  pprint.pprint(es.getNodes())


def test2(baseurl="https://cn.dataone.org/cn"):
  es = EnvironmentState(baseurl)
  pprint.pprint(es.getFormats())

def test3(baseurl="https://knb.ecoinformatics.org/knb/d1/mn"):
  ns = NodeState(baseurl)
  n = ns.count()
  print "{0} : {1}".format(baseurl, n)


def main(baseurl="https://cn.dataone.org/cn"):
  es = EnvironmentState(baseurl)
  es.populateState()
  print es
  

#===============================================================================
if __name__ == "__main__":
  logging.basicConfig(level=logging.DEBUG)
  test3()
  #test1()
  #test2()
  #main()
  

