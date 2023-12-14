import numpy as np
import requests
from datetime import datetime, time, timedelta
import socket

import aw_client

class DailyData():
    def __init__(self, data):
        self.data = data
        self.times15min = self.arr15min()
    
    # Extract a specifiy column(variable) from the data with the corresponding time values
    def columnData(self, field):
        datalength = len(self.data)
        allvalues = []
        alltimes = []
        # Extract all the column values
        for i in range(datalength):
            dataRow = self.data[i]
            value = dataRow[field]
            if value is not None:
                alltimes.append(self.formatDate(dataRow['created_at']))
                allvalues.append(value)
        return [alltimes, allvalues]
    
    ### ... RECURRENT FUNCTIONS ... ###
    # extract the time in the day (as a string)
    def formatDate(self, date):
        formatted_date = date[11:13] + date[14:16]
        return self.formatTime(formatted_date)

    # transform the time value into an integer, rounding to the nearest 5 minutes
    def formatTime(self, time):
        intTime = int(time)
        intTime = round(intTime / 5) * 5
        if intTime % 100 == 60:
            intTime += 40
        return intTime
    
    def arr15min(self):
        timearray = [0]
        i = 0
        while i <= 2340:
            # Update time counter
            if i % 100 == 45:
                i += 55
            else:
                i += 15
            timearray.append(i)
        return timearray
    
    def calculateAverage(arr):
        total = 0
        for value in arr:
            total += float(value)
        return round(total/len(arr), 2)
    
    def Closest15min(self, element):
        tweaked_element = (element % 100) % 15
        if tweaked_element == 5:
            element -= 5
        elif tweaked_element == 10:
            element += 5
        else:
            element = self.Closest15min(element+1)
        if (element % 100) == 60:
            element += 40
        return element
    
    def findTimeIndex(self, timearr, value):
        targetIndex = None
        for i in range(len(timearr)):
            if timearr[i] == value:
                targetIndex = i
                break  # Exit the loop once the first match is found
        return targetIndex

    def formatMoveData(self, data):
        moveallvalues = data[1]
        for index, element in enumerate(moveallvalues):
            element = element[1:] # Remove the buffer 2
            moveallvalues[index] = element
        return [data[0], moveallvalues]


### ... Luminosity Processing ... ###
class LightData(DailyData):
    def __init__(self, data):
        super().__init__(data)
        self.rawlightdata = DailyData.columnData(self, "field3")
        self.processedlightdata = self.processLightData()
        self.lightduration = self.LightDuration()

    def LightDuration(self):
        duration = 0
        for value in self.processedlightdata:
            if value != None and value >= 35:
                duration += 1
        duration = duration * 15
        total_light = (duration)/60
        return round(total_light, 2)



    def processLightData(self):
        lumavgvalues = [None] * len(self.times15min)
        lumalltimes = self.rawlightdata[0]
        lumallvalues = self.rawlightdata[1]

        # Cycle through all the values of time
        timelength = len(lumalltimes)
        timeindex = 1
        for i in range(timelength-2):
            if timeindex <= 95:
                intTime = lumalltimes[i]
                if i == 0:  # Deal with the first row
                    lumavgvalues[0] = DailyData.calculateAverage([lumallvalues[0], lumallvalues[1]])
                elif intTime == self.times15min[timeindex]:  # Deal with normal case
                    lumavgvalues[timeindex] = DailyData.calculateAverage([lumallvalues[i-1], lumallvalues[i], lumallvalues[i+1]])
                    timeindex += 1
                elif intTime > self.times15min[timeindex]:  # Deal with missing values
                    lumavgvalues[timeindex] = DailyData.calculateAverage([lumallvalues[i-1], lumallvalues[i]])
                    timeindex += 1
        return lumavgvalues

### ... Distraction Processing ... ###
class DistractionData(DailyData):
    def __init__(self, data):
        super().__init__(data)
        self.rawphonedata = DailyData.columnData(self, "field4")
        self.rawipaddata = DailyData.columnData(self, "field5")
        self.rawmovedata = self.formatMoveData(DailyData.columnData(self, "field7"))
        self.processedmoveamountdata = self.processMoveAmountData()
        self.processedmovedata = self.processMoveData()
        self.processeddevicedata = self.processDeviceData()
        self.distractiondata = self.processDistractionData()
        self.inroomduration = self.InRoomLength()

    def processDistractionData(self):
        result = [a + b for a, b in zip(self.processedmoveamountdata, self.processeddevicedata)]
        return result

    def processMoveAmountData(self):
        disvalues = [0] * len(self.times15min)

        # Add when I move around the house (== not sitting and working well)
        for index, element in enumerate(self.rawmovedata[0]):
            element = DailyData.Closest15min(self, element)
            valueIndex = DailyData.findTimeIndex(self, self.times15min, element)
            if valueIndex != None:
                disvalues[valueIndex] += len(self.rawmovedata[1][index])

        return disvalues
    
    def processDeviceData(self):
        disvalues = [0] * len(self.times15min)

        # Add when I open 'bad' app on my phone
        for index, element in enumerate(self.rawphonedata[0]):
            element = DailyData.Closest15min(self, element)
            valueIndex = DailyData.findTimeIndex(self, self.times15min, element)
            if valueIndex != None:
                disvalues[valueIndex] += int(self.rawphonedata[1][index])

        # Add when I open 'bad' app on my ipad
        for index, element in enumerate(self.rawipaddata[0]):
            element = DailyData.Closest15min(self, element)
            valueIndex = DailyData.findTimeIndex(self, self.times15min, element)
            if valueIndex != None:
                disvalues[valueIndex] += int(self.rawipaddata[1][index])

        return disvalues

    
    def processMoveData(self):
        moveavgvalues = [None] * len(self.times15min)

        movealltimes = self.rawmovedata[0]
        moveallvalues = self.rawmovedata[1]
        
        # Cycle through all the values of time, grouping by 15min
        timelength = len(movealltimes)
        timeindex = 1
        for i in range(timelength-2):
            if timeindex <= 95:
                intTime = movealltimes[i]
                if i == 0: # Deal with the first row
                    moveavgvalues[0] = moveallvalues[0] + moveallvalues[1]
                elif intTime == self.times15min[timeindex]: # Deal with normal case
                    moveavgvalues[timeindex] = moveallvalues[i-1] + moveallvalues[i] + moveallvalues[i+1]
                    timeindex += 1
                elif intTime > self.times15min[timeindex]: # Deal with missing values
                    moveavgvalues[timeindex] = moveallvalues[i-1] + moveallvalues[i]
                    timeindex += 1

        # Fill in as a step function
        currentstatus = 1
        for index, element in enumerate(moveavgvalues):
            if element == "":
                moveavgvalues[index] = currentstatus
            elif isinstance(element, str):
                moveavgvalues[index] = int(element[-1])
                currentstatus = int(element[-1])

        return moveavgvalues

    def InRoomLength(self):
        duration = 0
        for value in self.processedmovedata:
            if value == 1:
                duration += 1
        duration = duration * 15
        total_inroom = (duration)/60
        return round(total_inroom, 2)

        
class SleepData(DailyData):
    def __init__(self, data):
        super().__init__(data)
        self.rawmovedata = self.formatMoveData(DailyData.columnData(self, "field7"))
        self.rawphonedata = DailyData.columnData(self, "field4")
        self.processedsleepdata = self.processSleepData()
        self.sleepduration = self.sleepLength()

    def sleepLength(self):
        firssleepindex = self.processedsleepdata.index(1)
        for i in range(firssleepindex, len(self.processedsleepdata)):
            if self.processedsleepdata[i] != 1:
                lastsleepindex = i
                break
        duration = (lastsleepindex - firssleepindex) * 15
        total_sleep = (duration)/60
        return round(total_sleep, 2)

    
    def processSleepData(self):
        sleepvalues = [0] * len(self.times15min)
        # Add when I'm awake and moving in my room
        firstmoveindex = next((index for index, element in enumerate(self.rawmovedata[1]) if element != '' and self.rawmovedata[0][index]>500), None)
        firstmovetime = self.rawmovedata[0][firstmoveindex]
        movevalueIndex = DailyData.findTimeIndex(self, self.times15min, DailyData.Closest15min(self, firstmovetime))
        sleepvalues[movevalueIndex] = 1

        # Add my last phone of the day
        lastphonetime = self.rawphonedata[0][-1]
        phonevalueIndex = DailyData.findTimeIndex(self, self.times15min, DailyData.Closest15min(self, lastphonetime))
        if isinstance(phonevalueIndex, int):
            sleepvalues[phonevalueIndex] = 2

        #Check if yesterday's sleep time started early today morning
        sleep_begins = 0
        for element in self.rawphonedata[0]:
            if element<500:
                sleep_begins = element
        phonevalueIndex = DailyData.findTimeIndex(self, self.times15min, DailyData.Closest15min(self, sleep_begins))
        sleepvalues[phonevalueIndex] = 2


        if sleep_begins != 0:
            currentstatus = 0
        else:
            currentstatus = 1

        for index, element in enumerate(sleepvalues):
            if currentstatus != 0 and element == 0:
                sleepvalues[index] = currentstatus
            elif element == 2:
                currentstatus = 1
                sleepvalues[index] = 1
            elif element == 1:
                currentstatus = 0

        return(sleepvalues)
        

class KeyboardData(DailyData):
    def __init__(self, date):
        super().__init__(None)
        self.rawdata = self.getBucket(date)
        self.processedworkdata = self.formatAfkData()
        self.workduration = self.dailyProductivity()

    def getBucket(self, date):
        bucket_id = f"aw-watcher-afk_{socket.gethostname()}"

        daystart = datetime(int(date[0:4]), int(date[5:7]), int(date[8:10]), 0, 0, 0)
        dayend = daystart + timedelta(days=1)

        awc = aw_client.ActivityWatchClient("testclient")
        events = awc.get_events(bucket_id, start=daystart, end=dayend)
        self.veryrawdata = events
        afkData = [[0], [0]]
        for e in reversed(events):
            duration = int(e['duration'].total_seconds())
            status = e['data']['status']
            if duration > 60 and status != afkData[1][-1]:
                etime = e['timestamp'].strftime('%H:%M')
                afkData[0].append(int(etime[0:2]+etime[3:5]))
                afkData[1].append(status)
        afkData = [afkData[0][1:], afkData[1][1:]]
        return afkData
    
    def formatAfkData(self):
        afkvalues = [None] * len(self.times15min)
        for index, element in enumerate(self.rawdata[0]):
            valueIndex = DailyData.findTimeIndex(self, self.times15min, DailyData.Closest15min(self, element))
            if afkvalues[valueIndex] == None:
                afkvalues[valueIndex] = ""
            if self.rawdata[1][index] == 'afk':
                afkvalues[valueIndex] += "0"
            elif self.rawdata[1][index] == 'not-afk':
                afkvalues[valueIndex] += "1"

        if self.rawdata[1][0] == "afk":
            currentstatus = 0
        elif self.rawdata[1][0] == "not-afk":
            currentstatus = 1

        for index, value in enumerate(afkvalues):
            if value == None:
                afkvalues[index] = currentstatus
            elif isinstance(value, str):
                value = [int(char) for char in value]
                afkvalues[index] = round(DailyData.calculateAverage(value))
                currentstatus = value[-1]
        return afkvalues
    
    def dailyProductivity(self):
        events = [e for e in self.veryrawdata if e.data["status"] == "not-afk"]
        total_duration = sum((e.duration for e in events), timedelta())
        total_hours = (total_duration.total_seconds() / 60)/60
        return round(total_hours, 2)
                

def DayData(date):
    url = "https://api.thingspeak.com/channels/2320730/feeds.json?api_key=M27V5SG8IEU5CRMH&start=" + date + "%2000:00:00&end=" + date + "%2023:59:59"
    response = requests.get(url)
    response = response.json()
    raw_data = response['feeds']

    lightData = LightData(raw_data)
    distractionData = DistractionData(raw_data)
    workData = KeyboardData(date)
    sleepData = SleepData(raw_data)

    timestamp = distractionData.times15min
    for index, time in enumerate(timestamp):
        timestamp[index] = date + ' ' + formatTimeString(time)

    processeddata = {
        'timestamp': timestamp,
        'lightDataset': lightData.processedlightdata,
        'lightduration': lightData.lightduration,
        'disDataset': distractionData.distractiondata,
        'whereDataset': distractionData.processedmovedata,
        'inroomduration': distractionData.inroomduration,
        'sleepDataset':sleepData.processedsleepdata,
        'sleepduration': sleepData.sleepduration,
        'workDataset': workData.processedworkdata,
        'workduration': workData.workduration
    }
    
    return processeddata

def formatTimeString(time):
    time = str(time)
    time = time.zfill(4)
    time = time[0:2] + ":" + time[2:4]
    return time

### Testing the data processing here:
# data = DayData("2023-12-11")
# print (data['lightDataset'])
# keydata = KeyboardData("2023-11-22")
# print(keydata.workduration)


