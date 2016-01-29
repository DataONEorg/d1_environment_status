/****
 * JD and MJD routines
 * 
 */

Date.prototype.getJD = function() {
  return this.getTime()/86400000 + 2440587.5;
}

Date.prototype.getMJD = function() {
  return this.getJD()-2400000.5;
}

function dateFromJD(jd) {
  var tstamp = (jd - 2440587.5) * 86400000;
  return new Date(tstamp);
}

function dateFromMJD(mjd) {
  var jd = mjd + 2400000.5;
  return dateFromJD(jd);
}


