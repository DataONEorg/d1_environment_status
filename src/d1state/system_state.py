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
import httplib
import math
from d1_client import cnclient, cnclient_1_1


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


class EnvironmentState(object):
  #increment the version flag if there's a change to the generated data structure  
  VERSION = "14"
  COUNT_PUBLIC = None
  COUNT_PUBLIC_CURRENT = "-obsoletedBy:[* TO *]"
  TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.0+00:00"
  JS_VARIABLE_STATE = "var env_state = "
  JS_VARIABLE_INDEX = "var env_state_index = "
  
  def __init__(self, baseurl, cert_path=None):
    self.log = logging.getLogger(str(self.__class__.__name__))
    self.log.debug("Initializing...")
    self.baseurl = baseurl
    self.state = {'meta':None,
                  'formats':None,
                  'nodes':None,
                  'counts':None,
                  'summary': None
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
    self.state['counts'] = self.getCounts()
    self.state['summary'] = self.summarizeCounts()
    self.state['summary']['sizes'] = self.getObjectTypeSizeHistogram()
    

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
                }
      sync = node.synchronization
      if not sync is None:
        entry['sync.schedule'] = syncschedule_array(sync.schedule)
        entry['sync.lastHarvested'] = sync.lastHarvested.strftime("%Y-%m-%d %H:%M:%S.0%z")
        entry['sync.lastCompleteHarvest'] = sync.lastCompleteHarvest.strftime("%Y-%m-%d %H:%M:%S.0%z")        
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
    query='q'
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
          results = eval(self.clientv1.query("solr", query="q", 
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


def main(baseurl="https://cn.dataone.org/cn"):
  es = EnvironmentState(baseurl)
  es.populateState()
  print es
  

#===============================================================================
if __name__ == "__main__":
  logging.basicConfig(level=logging.DEBUG)
  #test1()
  #test2()
  #main()
  

