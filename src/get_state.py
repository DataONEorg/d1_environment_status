'''
Created on Mar 2, 2014

@author: vieglais
'''

import os
import errno
import logging
from yaml import load, Loader
from optparse import OptionParser
from d1state.system_state import EnvironmentState
import json
import pprint


def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc:
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: 
      raise


def loadConfig(config_file):
  
  def getConfigValue(config, keys, default=None, index=None):
    if index is None:
      index = len(keys)-1
    if index == 0:
      try:
        return config[keys[index]]
      except:
        return default
    try:
      res = getConfigValue(config[keys[index]], 
                            keys, 
                            default=default, 
                            index=index-1)
      return res
    except KeyError as e:
      logging.error("Missing key: {0:s}".format(e))
      return default

  config = {}
  try:
    config = load(file(config_file, 'r'), Loader=Loader)
  except:
    logging.info("Error loading config file: {0:s}".format(config_file))
  res = {}
  res['statefolder'] = getConfigValue(config, 
                                     ['dest', 'state'], 
                                     default=os.path.join(os.environ['HOME'], ".dataone/state"))
  res['baseurl'] = getConfigValue(config, 
                                     ['baseurl', 'state'], 
                                     default="https://cn.dataone.org/cn")
  res['name'] = getConfigValue(config, 
                                     ['name', 'state'], 
                                     default="Production Environment")
  res['stateformat'] = getConfigValue(config, 
                                     ['destformat', 'state'], 
                                     default="%Y%m%dT%H%M%S.js")
  return res


def main(config):
  mkdir_p(config['statefolder'])
  #load index JSON
  state_index_src = os.path.join(config['statefolder'], "index.js")
  logging.debug("INDEX = " + state_index_src)
  state_index = []
  try:
    jstr = file(state_index_src, "r").read()
    state_index = json.loads(jstr[len(EnvironmentState.JS_VARIABLE_INDEX):])
  except:
    logging.info("No index file available. Creating at {0:s}".format(state_index_src))
  
  #capture state
  envstate = EnvironmentState(config['baseurl'])
  envstate.populateState()
  #append index entry
  row = [envstate.getTStamp(), envstate.tstamp.strftime(config['stateformat'])]
  logging.debug(pprint.pformat(row))
  state_index.append(row)
  #Write out the state JSON file
  statedest = file(os.path.join(config['statefolder'],row[1]), "w")
  envstate.asJSON(statedest)
  statedest.close()
  #update the index JSON file
  jbuffer = file(state_index_src, "w")
  jbuffer.write(EnvironmentState.JS_VARIABLE_INDEX)
  json.dump(state_index, jbuffer, indent=2)
  jbuffer.close()



if __name__ == "__main__":
  CONFIG = os.path.join(os.environ['HOME'],".dataone/cache.conf")
  parser = OptionParser()
  parser.add_option("-l","--log",dest="loglevel",
                    help="1=DEBUG, 2=INFO, 3=WARN, 4=ERROR, 5=FATAL",
                    default=1, type="int")
  parser.add_option("-c","--config", dest="config",
                    help="Path to configuration file ({0:s})".format(CONFIG),
                    default=CONFIG)
  parser.add_option("-d","--detail", dest="doDetail",
                    help="Generate a detail set of counts (False)",
                    default=False, action="store_true")
  parser.add_option("-x","--nodownload", dest="doDownload",
                    help="Don't download new data if a cache is available (False)",
                    default=False, action="store_true")
  (options, args) = parser.parse_args()
  if options.loglevel < 1:
    options.loglevel = 1
  if options.loglevel > 5:
    options.loglevel = 5   
  logging.basicConfig(level=10*options.loglevel)
  config = loadConfig(options.config)
  logging.debug(pprint.pformat(config))
  main(config)
  