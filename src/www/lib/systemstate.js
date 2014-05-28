var DATA_FOLDER = "data";
var VIZ_READY = false;
var MAX_CHECKS = 10;
var DATA_READY_CHECKS = 0;
var VIZ_READY_CHECKS = 0;
var CURRENT_DATA_PAGE_INDEX = 0;

try {
  google.setOnLoadCallback(visualizationReady);
  google.load("visualization", "1", {
    packages : [ "corechart" ]
  });
} catch (e) {
  console.log(e);
  console.log('Google visualizations not available.');
}

function isDataReady() {
  return !(typeof env_state == 'undefined');
}

function isVizReady() {
  return VIZ_READY
}

/**
 * Uses the Google Visualization API to generate a histograms of content size.
 */
function renderSizeHistogram(otype, targetdiv, title, units, scaler, hLog) {
  //Display a histogram for object sizes
  var data = new google.visualization.DataTable();
  data.addColumn('number', 'Size');
  data.addColumn('number', 'Counts');
  data.addColumn({
    type : 'string',
    role : 'style'
  });
  for ( var i = 0; i < env_state.summary.sizes[otype].histogram.length; i++) {
    var row = env_state.summary.sizes[otype].histogram[i];
    var a = (row[0] + row[1]) / (2 * scaler);
    var b = row[2];
    data.addRow([ a, b, "#888888" ]);
    //console.log(row);
    //console.log(a + "  " + b);
  }
  //var view = new google.visualization.DataView(data);
  //view.setColumns()
  htitle = "Size (" + units + ")";
  var options = {
    title : title,
    legend : {
      position : 'none'
    },
    vAxis : {
      logScale : true,
      title : "Count",
      gridlines : {
        count : 4
      }
    },
    hAxis : {
      logScale : hLog,
      title : htitle,
      gridlines : {
        count : -1
      }
    }
  }
  var chart = new google.visualization.ColumnChart(document
      .getElementById(targetdiv));
  chart.draw(data, options)
}

function renderHistograms() {
  renderSizeHistogram("data", "histogram.data",
      "Public Data Objects (Log scales)", "MB", 1024 * 1024, true);
  renderSizeHistogram("metadata", "histogram.metadata",
      "Public Metadata Objects (Log scales)", "KB", 1024, true);
  renderSizeHistogram("resource", "histogram.resource",
      "Public Resource Maps (Log scales)", "KB", 1024, true);
}

function doRenderVisualizations() {
  if (!isDataReady()) {
    VIZ_READY_CHECKS++;
    if (VIZ_READY_CHECKS < MAX_CHECKS) {
      setTimeout(doRenderVisualizations, 100);
    } else {
      $("#histograms").hide();
    }
  } else {
    renderHistograms();
  }
}

function visualizationReady() {
  console.log("Visualization loaded.")
  VIZ_READY = true;
  doRenderVisualizations()
}

function getParameterByName(name) {
  name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
  var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"), results = regex
      .exec(location.search);
  return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g,
      " "));
}

function dataLoadError(jqxhr, settings, exception) {
  console.log("Error loading javascript");
}

function jq(someid) {
  return someid.replace(/(:|\.|\[|\])/g, "\\$1");
}

function nowUTC() {
  var t = new Date();
  return new Date(t.getUTCFullYear(), t.getUTCMonth(), t.getUTCDate(), t
      .getUTCHours(), t.getUTCMinutes(), t.getUTCSeconds(), t
      .getUTCMilliseconds())
}

function dateDelta(t0, t1) {
  //Return array of [days, hours, minutes, seconds] between t0 and t1
  console.log("t0 = " + t0);
  t0 = t0.getTime();
  console.log("t0 a = " + t0);
  console.log("t1 = " + t0);
  t1 = t1.getTime();
  console.log("t1 a= " + t0);
  
  var msechour = 1000 * 60 * 60;
  var dt = t1 - t0;
  var res = [ 0, 0, 0, 0 ];
  res[0] = Math.floor(dt / (msechour * 24));
  dt = dt - res[0] * msechour * 24;
  res[1] = Math.floor(dt / msechour);
  dt = dt - res[1] * msechour;
  res[2] = Math.floor(dt / (1000 * 60));
  dt = dt - res[2] * 1000 * 60;
  res[3] = Math.floor(dt / 1000);
  return res;
}

function dateDeltaStr(t0, t1) {
  var dt = dateDelta(t0, t1);
  if (dt[0] > 1000) {
    return "Never";
  }
  if (dt[0] > 10) {
    return dt[0] + " days";
  }
  if (dt[0] > 0) {
    return dt[0] + " days, " + dt[1] + " hours";
  }
  return dt[1] + "h " + dt[2] + "m " + dt[3] + "s";
}

function renderNodeTable() {
  var i = 1;
  var tnow = nowUTC();
  for ( var key in env_state.nodes) {
    if (env_state.nodes[key].type == "mn") {
      var tr = $("<tr>");
      if (env_state.meta.version == "1.1.0") {
        tr.attr("class", "mntable");
      } else {
        if (env_state.nodes[key].state) {
          tr.attr("class", "mntable");
        } else {
          tr.attr("class", "mntable offline");
        }
      }

      console.log(tr);
      tr.append($("<td>").text(i));
      tr.append($("<td>").text(key));
      tr.append($("<td>").text(env_state.nodes[key].baseurl));
      dtd = $("<td>");
      dtd.attr("title", env_state.nodes[key].description);
      dtd.text(env_state.nodes[key].name);
      tr.append(dtd);
      var tsync = env_state.nodes[key]["sync.lastHarvested"];
      tsync = $.trim(tsync);
      tsync = tsync.replace("++", "+");
      tsync = tsync.replace(" ", "T");
      tsync = tsync.replace("+0000", "Z");
      tsync = new Date(tsync);
      tr.append($("<td>").text(dateDeltaStr(tsync, tnow)));
      $("[id=d1\\.nodes_table]").append(tr);
      i++;
    }
  }
}


function renderDNSInfo() {
  if (parseInt(env_state.meta.version) < 16 ) {
    $("#d1_dns").hide();
    return;
  }
  $("#d1_dns").show();
  //TODO: Generalize this
  var target = $("[id=d1\\.dnsinfo]");
  var prodips = env_state.dns['cn.dataone.org'].address;
  for (var key in env_state.dns) {
    if (key != 'cn.dataone.org') {
      var entry = $("<span>");
      entry.addClass('spaced');
      entry.text(key.split(".")[0]);
      var ip = env_state.dns[key].address[0];
      entry.attr("title", ip); 
      if ($.inArray(ip, prodips) >= 0) {
        entry.addClass('embolden');
      } else {
        entry.addClass('deemphasize');
      }
      target.append(entry);
    }
  }
}

function renderData(data, textStatus, jqxhr) {
  $("[id^=d1\\.]").each(function(index, element) {
    var keys = element.id.split(".");
    var newv = env_state;
    for ( var i = 1; i < keys.length; i++) {
      newv = newv[keys[i]]
    }
    $("[id=" + jq(element.id) + "]").text(newv);
  });
  renderNodeTable();
  renderDNSInfo();
}

/**
 Called when a request to loadData() completes successfully. Initiates 
 rendering of the laoded system state record.
 */
function loadLatestDataSuccess(data, textStatus, jqxhr) {
  //data object retrieved, but may not yet be ready to use
  //If not, then set a timeout to check again in a bit 
  if (!isDataReady()) {
    if (DATA_READY_CHECKS < MAX_CHECKS) {
      setTimeout(loadLatestDataSuccess, 200);
    } else {
      console.log("ERROR: unable to load data for rendering.");
    }
  } else {
    renderData(data, textStatus, jqxhr);
    //Rendering of the visualizations is dependent on some calculations 
    //performed on the loaded data
    setTimeout(doRenderVisualizations, 50);
  }
}

/**
 Initiates asynchronous loads of the specified system state record
 */
function loadData(data_entry) {
  if (typeof data_entry == 'undefined') {
    CURRENT_DATA_PAGE_INDEX = env_state_index.length - 1;
    data_entry = env_state_index[CURRENT_DATA_PAGE_INDEX][1];
  }
  $("#" + jq(data_entry)).toggleClass("selected");
  $.getScript(DATA_FOLDER + "/" + data_entry, loadLatestDataSuccess).fail(
      dataLoadError);
}

/**
 Clears any rendering of a system state record from the view.
 */
function clearPage() {
  $("#data_index_table tr td").removeClass("selected");
  DATA_READY_CHECKS = 0;
  VIZ_READY_CHECKS = 0;
  $("[id^=d1\\.]").each(function(index, element) {
    $(this).text("");
  });
  $("[id=d1\\.nodes_table]").find("tr").remove();
}

/**
 Loads the list of available system state records from the json file 
 included by this page (data/index.js).
 */
function populateIndex() {
  var itable = $("#data_index_table");
  for ( var i = 0; i < env_state_index.length; i++) {
    var tr = $("<tr>");
    var td = $("<td>").text(env_state_index[i][0]);
    td.attr("id", env_state_index[i][1]);
    td.click(function(element) {
      var js = $(this).attr("id");
      //console.log(js);
      clearPage();
      loadData(js)
    });
    tr.prepend(td);
    itable.append(tr);
  }
}

/**
 Load the system state record that one older or newer than the 
 current record.
 */
function nextDataPage(increment) {
  if (increment > 0) {
    if (CURRENT_DATA_PAGE_INDEX < env_state_index.length - 1) {
      CURRENT_DATA_PAGE_INDEX += 1;
      clearPage();
      loadData(env_state_index[CURRENT_DATA_PAGE_INDEX][1]);
      return;
    }
  }
  if (increment < 0) {
    if (CURRENT_DATA_PAGE_INDEX > 0) {
      CURRENT_DATA_PAGE_INDEX = CURRENT_DATA_PAGE_INDEX - 1;
      clearPage();
      loadData(env_state_index[CURRENT_DATA_PAGE_INDEX][1]);
      return;
    }
  }
}

/**
 Respond to right and left arrow keys to step through the list of available
 system state records.
 */
$(document).keydown(function(e) {
  if (e.keyCode == 37) {
    //left key pressed
    nextDataPage(-1);
    return false;
  }
  if (e.keyCode == 39) {
    //right key pressed
    nextDataPage(1);
    return false
  }
});
