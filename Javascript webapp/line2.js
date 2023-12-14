// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#292b2c';


// PROCESS ALL DATA FROM THINGSPEAK ____________________________________________________

function getDailyData (date) {
  let responseData;
  url = "https://api.thingspeak.com/channels/2320730/feeds.json?api_key=M27V5SG8IEU5CRMH&start=" + date + "%2000:00:00&end=" + date + "%2023:59:59"
  return fetch(url)
    .then((response) => {
      return response.json();
    });
}

// created_at, entry_id, field1(temp), field2(humidity), field3(luminosity), field4(Phone), field5(Ipad)
function columnData(data, field) {
  datalength = Object.keys(data).length;
  let allvalues = [];
  let alltimes = [];
  // Extract all the column values
  for (let i = 0; i <= (datalength-1); i++) {
    dataRow = data[i]
    value = dataRow[field]
    if (value !== null) {
      alltimes.push(formatDate(dataRow['created_at']))
      allvalues.push(value)
    }
  }
  return [alltimes, allvalues]
}


// .... LUMINOSITY .... //
function processDataLum(data) {
  let [lumalltimes, lumallvalues] = columnData(data, "field3")

  let times15min = arr15min();
  let lumavgvalues = Array(times15min.length).fill(null);

  // Cycle through all the values of time
  timelength = lumalltimes.length
  timeindex = 1
  for (let i = 0; i <= (timelength-1); i++) {
      intTime = lumalltimes[i]
      if (i == 0) { // Deal with the first row
        lumavgvalues[0] = calculateAverage([lumallvalues[0], lumallvalues[1]])
      } else if (intTime == times15min[timeindex]) { // Deal with normal case
        lumavgvalues[timeindex] = calculateAverage([lumallvalues[i-1],lumallvalues[i],lumallvalues[i+1]])
        timeindex += 1
      } else if (intTime > times15min[timeindex]){ // Deal with missing values
        lumavgvalues[timeindex] = calculateAverage([lumallvalues[i-1],lumallvalues[i]])
        timeindex += 1
      }
  };

  return {
    timestamp: times15min,
    lumvalues: lumavgvalues
  }
}

// .... DEVICES .... //
function processDataDev(data) {
  // Goal is to flag whenever I open an app or close it
  let [phonealltimes, phoneallvalues] = columnData(data, "field4")
  let [ipadalltimes, ipadallvalues] = columnData(data, "field5")

  let times15min = arr15min();
  let devvalues = Array(times15min.length).fill(0); 

  phonealltimes.forEach(function(element,index) {          
    // Transform values to match closest 15 min mark
    element = MakeClosest15mark(element)
    if (devvalues[findTimeIndex(times15min, element)] == null) {
      devvalues[findTimeIndex(times15min, element)] = parseInt(phoneallvalues[index])
    } else {
      devvalues[findTimeIndex(times15min, element)] += parseInt(phoneallvalues[index])
    }
  })

  ipadalltimes.forEach(function(element,index) {          
    // Transform values to match closest 15 min mark
    element = MakeClosest15mark(element)
    if (devvalues[findTimeIndex(times15min, element)] == null) {
      devvalues[findTimeIndex(times15min, element)] = parseInt(phoneallvalues[index])
    } else {
      devvalues[findTimeIndex(times15min, element)] += parseInt(phoneallvalues[index])
    }
  })

  return {
    timestamp: times15min,
    devvalues: devvalues
  }
}


// .... SLEEP .... //
function processDataSleep(data) {
  let [sleepalltimes, sleepallvalues] = columnData(data, "field6")

  let times15min = arr15min();
  let sleepvalues = Array(times15min.length).fill(0);

  sleepalltimes.forEach((element) => {
    sleepvalues[findTimeIndex(times15min, MakeClosest15mark(element))] = 1
  })
  return {
    sleepvalues: sleepvalues
  }
}

// .... MOVEMENT .... //
function processDataMovement(data) {
  let [movealltimes, moveallvalues] = columnData(data, "field7")

  let times15min = arr15min();
  let moveavgvalues = Array(times15min.length).fill(null);

  // Format the array of values
  moveallvalues.forEach((element, index) => {
    element = element.slice(1) // Remove the buffer 2
    moveallvalues[index] = element
  })

  // Cycle through all the values of time, grouping by 15min
  timelength = movealltimes.length
  timeindex = 1
  for (let i = 0; i <= (timelength-1); i++) {
      intTime = movealltimes[i]
      if (i == 0) { // Deal with the first row
        moveavgvalues[0] = moveallvalues[0] + moveallvalues[1]
      } else if (intTime == times15min[timeindex]) { // Deal with normal case
        moveavgvalues[timeindex] = moveallvalues[i-1] + moveallvalues[i] + moveallvalues[i+1]
        timeindex += 1
      } else if (intTime > times15min[timeindex]){ // Deal with missing values
        moveavgvalues[timeindex] = moveallvalues[i-1] + moveallvalues[i]
        timeindex += 1
      }
  };

  // Fill in as a step function
  let currentstatus = 1
  moveavgvalues.forEach((element, index) => {
    if (element == "") {
      moveavgvalues[index] = currentstatus
    } else {
      moveavgvalues[index] = element.length
      currentstatus = parseInt(element[element.length - 1])
    }
  })

  return {
    movevalues: moveavgvalues
  }
}


// .... BUILDING BLOCKS .... //
function arr15min() {
  let timearray = [0];
  for (i = 0; i<=2340;) {
    // Update time counter
    if (i % 100 == 45) {
      i += 55
    } else {
      i += 15
    }
    timearray.push(i)
  }
  return timearray
}

function MakeClosest15mark(element) {
  tweakedelement = (element % 100) % 15
  if (tweakedelement == 5) {
    element -= 5
  } else if (tweakedelement == 10) {
    element += 5
  } else {
    element = MakeClosest15mark(element+1)
  }
  if ((element % 100) == 60) {
    element += 40
  }
  return element
}

function findTimeIndex(timearr, value) {
  for (let i = 0; i < timearr.length; i++) {
    if (timearr[i] === value) {
      targetIndex = i;
      break; // Exit the loop once the first match is found
    }
  }
  return targetIndex
}

function formatDate(date) {
  let formattedDate = date.substring(11, 13) + date.substring(14, 16);
  return formatTime(formattedDate)
}

function formatTime(time) {
  intTime = parseInt(time)
  intTime = Math.round(intTime / 5) * 5;
  if (intTime % 100 == 60) {
    intTime += 40
  }
  return intTime
}

function calculateAverage(arr) {
  let sum = arr.reduce((total, value) => total + parseFloat(value), 0);
  return sum / arr.length;
}


// .... AFK (away from keyboard) .... //
// Handle afk at each window loading
let afkData = localStorage.getItem("afk_data")
afkData = JSON.parse(afkData)
afkStepFunction = makeStepFunction(afkData, "not-afk", "afk")
console.log(afkStepFunction)

function getDates(data) {
  let datearray = [0]
  console.log(data)
  data.forEach((element) => {
    if (element[0] != datearray[datearray.length-1]) {
      datearray.push(element[0])
    }
  })
  return datearray.slice(1)
}

function makeStepFunction(data, posvalue, negvalue) {
  let times15min = arr15min();

  afkDates = getDates(data)
  let afkDailyData = {}
  afkDates.forEach((element) => {
    afkDailyData[element] = Array(times15min.length).fill(null);
  })
  console.log(afkDailyData)

  data.forEach((element) => {
    console.log(MakeClosest15mark(element[1]))
    valueLocation = findTimeIndex(times15min, MakeClosest15mark(element[1]))
    if (afkDailyData[element[0]][valueLocation] === null) {
      afkDailyData[element[0]][valueLocation] = ""
    }
    if (element[3] == posvalue) {
      afkDailyData[element[0]][valueLocation] += "1"
    } else if (element[3] == negvalue) {
      afkDailyData[element[0]][valueLocation] += "0"
    }
  })

  afkDates.forEach((key) => {
    let currentstatus = 0
    afkDailyData[key].forEach((element, index) => {
      if (element === null) {
        afkDailyData[key][index] = currentstatus
      } else if (typeof(element) == "string") {
        element = Array.from(element, char => parseInt(char, 10))
        afkDailyData[key][index] = Math.round(calculateAverage(element))
        currentstatus = element[element.length - 1]
      }
    })
  })

  return afkDailyData
}



// _________________________________________________________________________________

function updateGraph (graph, xdata, y1data, y2data, y3data, y4data, y5data) {
  
  // Area Chart Example
  var ctx = document.getElementById(graph)
  console.log("making " + graph)
  var line = new Chart(ctx, {
    type: 'line',
    data: {
        datasets: [{
            // Light
            label: 'Luminosity (Lux) - ',
            data: y1data,
            type: 'line',
            yAxisID: 'y-axis-1',
            borderColor:"blue",
            fill: false,
            pointRadius: 5,
            },
            // Productivity
            {
            label: "Device use ('bad' apps opened)",
            data: y2data,
            type: 'line',
            steppedLine: true,
            yAxisID: 'y-axis-2',
            borderColor:"rgba(204,102,0,1)",
            borderWidth:1,
            pointRadius: 0,
            fill: true,
            backgroundColor: "rgba(204,102,0,0.5)",
            },
            // {
            // label: 'Working on Keyboard',
            // data: y3data,
            // type:'line',
            // steppedLine: true,
            // yAxisID: 'y-axis-3',
            // borderColor: "rgba(117,194,120,1)",
            // borderWidth:1,
            // pointRadius: 0,
            // fill:true,
            // backgroundColor: "rgba(117,194,120,0.2)",
            // },
            // // Sleep
            // {
            // label: 'Waking up',
            // data: y4data,
            // type:'line',
            // steppedLine: true,
            // yAxisID: 'y-axis-3',
            // borderColor: "grey",
            // borderWidth:1,
            // pointRadius: 0,
            // fill:true,
            // backgroundColor: "grey",
            // },
            // Movements
            {
            label: "Moving",
            data: y5data,
            type: 'line',
            yAxisID: 'y-axis-2',
            borderColor:"rgba(117,194,120,0.8)",
            borderWidth:1,
            pointRadius: 0,
            fill: true,
            backgroundColor: "rgba(117,194,120,0.8)",
            }
        ],//end data sets
        labels: xdata
    },//end data
    options: {
      scales: {
        xAxes: [{
          position: "bottom",
          gridLines: {
            display: false
          },
      }],
        yAxes: [{
          id: 'y-axis-1',
          type: 'linear',
          position: 'left',
          gridLines: {
            color: "rgba(0, 0, 0, .125)",
          }
        },{
          id: 'y-axis-2',
          type: 'linear',
          position: 'right',
          ticks:{
            max: 6,
            min: 0,
            display: false
          },
          gridLines: {
            display: false
          },
        },{
          id: 'y-axis-3',
          type: 'linear',
          position: 'right',
          ticks:{
            max: 0.9,
            min: 0.1,
            display: false
          },
          gridLines: {
            display: false
          },
        }],
      },
      legend: {
        display: true
      }
    }
  });

}

// ___________________________________________________________________________

NbOfGraphs = 5

// // GET A LIST OF DATES
// // Create a new Date object
// let today = new Date();
// // Get the last 4 days dates in an array
// let graphDates = [];
// for (let i = 1; i <= NbOfGraphs; i++) {
//   // Subtract one day (in milliseconds)
//   let yesterday = new Date(today);
//   yesterday.setDate(today.getDate() - i);

//   // Get the current date components
//   let year = yesterday.getFullYear();
//   let month = yesterday.getMonth() + 1; // Months are zero-based, so we add 1
//   let day = yesterday.getDate();
//   // Format the date as a string (optional)
//   let todayDate = `${year}-${month < 10 ? '0' : ''}${month}-${day < 10 ? '0' : ''}${day}`;
//   graphDates.push(todayDate)
// }
graphDates = ["2023-11-23", "2023-11-22", "2023-11-21", "2023-11-19", "2023-11-20"]
console.log(graphDates)


// ADD THE GRAPH ELEMENTS TO THE PAGE
let graphSection = document.getElementById('graphSection');

for (let i = 1; i <= NbOfGraphs; i++) {
  let newGraph = document.createElement('div');
  newGraph.classList.add("col-lg-10")
  newGraph.innerHTML = `
    <div class="col-lg-10">
      <div class="card mb-3">
      <div class="card-header">
        Luminosity (Lux) vs Time - ${graphDates[i-1]}</div>
      <div class="card-body">
          <canvas id="line${i}"></canvas>
        </div>
      </div>
    </div>
  `;

  graphSection.appendChild(newGraph);
}


// ADD DATA IN THE GRAPHS
for (let i = 1; i <= NbOfGraphs; i++) {
  console.log("graph" + i)
  getDailyData(graphDates[i-1])
  .then(data => {
    console.log("doing " + i)
    lumdataset = processDataLum(data['feeds'])
    devdataset = processDataDev(data['feeds'])
    // sleepdataset = processDataSleep(data['feeds'])
    movedataset = processDataMovement(data['feeds'])
    // try {
    //   console.log(afkStepFunction[graphDates[i-1]].length)
    //   compdataset = afkStepFunction[graphDates[i-1]]
    // } catch (TypeError) {
    //   compdataset = Array(1441).fill(0)
    // }
    return {
      timestamp: lumdataset.timestamp,
      lumvalues: lumdataset.lumvalues,
      devvalues: devdataset.devvalues,
      // compvalues: compdataset,
      // sleepvalues: sleepdataset.sleepvalues,
      movevalues: movedataset.movevalues
    }
  })
  .then((dataset) => {
    console.log(dataset)
    // updateGraph(("line"+i), dataset.timestamp, dataset.lumvalues, dataset.devvalues, dataset.compvalues, dataset.sleepvalues, dataset.movevalues)
    updateGraph(("line"+i), dataset.timestamp, dataset.lumvalues, dataset.devvalues, dataset.devvalues, dataset.devvalues, dataset.movevalues)
  })
}

