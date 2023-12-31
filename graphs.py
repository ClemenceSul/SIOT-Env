### IMPORTS
import pandas as pd
from dataProcessing import DayData
import seaborn as sn
import matplotlib.pyplot as plt

# In this file, uncomment the line underneath the function to see the graphs of that function. 
# Feel free to change the dates. As a reminder, data collected between the 20th of November to the 24th of November had no actuations. Data collected from the 27th of November to the 1st of December had an actuation.

# Gets the data of the day. Return either the correlation between the parameters or the amount dedicated to each.
def getDailyCor(date, type="default"):
    data = DayData(date)

    if type == "default":
        del data['timestamp']
        del data['workduration']
        del data['sleepduration']
        del data['lightduration']
        del data['inroomduration']
        df = pd.DataFrame(data)
        corr_matrix = df.corr()
        return corr_matrix
    elif type == "length":
        del data['timestamp']
        return {
            "work": data['workduration'],
            "sleep": data['sleepduration'],
            "distractions": sum(data['disDataset']),
            "light": data["lightduration"],
            "inroom": data["inroomduration"]
        } 


### --- Get the correlation between the parameters on one day --- ###
def OneDay(date):
    corr_matrix = getDailyCor(date)
    sn.heatmap(corr_matrix, annot=True)
    plt.show()

# OneDay("2023-11-20")

### --- Get the average correlation between parameters over a week --- ###
def WeekAverage(datearr):
    week_corr = (getDailyCor(datearr[0]) + getDailyCor(datearr[1]) + getDailyCor(datearr[2]) + getDailyCor(datearr[3]) + getDailyCor(datearr[4])) / 5
    sn.heatmap(week_corr, annot=True)
    plt.show()

# WeekAverage(["2023-11-20", "2023-11-21", "2023-11-22", "2023-11-23", "2023-11-24"])


### --- Get the evolution of the correlation between the light and work datasets over a week --- ###
def WeekLightWork(datearr):
    week_corr = [getDailyCor(datearr[0]).iloc[4, 0]*100, getDailyCor(datearr[1]).iloc[4, 0]*100, getDailyCor(datearr[2]).iloc[4, 0]*100, getDailyCor(datearr[3]).iloc[4, 0]*100, getDailyCor(datearr[4]).iloc[4, 0]*100]
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    plt.plot(weekdays, week_corr, marker='o')
    plt.xlabel('Days')
    plt.ylabel('Correlation Coefficient (%)')
    plt.title('Light vs Work correlation coefficients over a week from 20th to 24th')
    # Annotating each point with its value
    # for x, y in zip(weekdays, week_corr):
    #     plt.text(x, y, f'({int(y)})', ha='left', va='bottom', color='blue', fontsize=8)

    plt.show()

# WeekLightWork(["2023-11-20", "2023-11-21", "2023-11-22", "2023-11-23", "2023-11-24"])


### --- Get the average correlation between parameters over a weekend --- ###
def WeekendAverage(datearr):
    weekend_corr = (getDailyCor(datearr[0]) + getDailyCor(datearr[1])) / 2
    sn.heatmap(weekend_corr, annot=True)
    plt.show()

# WeekendAverage(["2023-11-25", "2023-11-26"])

### --- Line graph of amounts spent on each parameter, and correlation between the amount attributed to each parameters --- ###
def WeekAmounts(datearr):
    # Extract keys and values
    dict1 = getDailyCor(datearr[0], type="length")
    dict2 = getDailyCor(datearr[1], type="length")
    dict3 = getDailyCor(datearr[2], type="length")
    dict4 = getDailyCor(datearr[3], type="length")
    dict5 = getDailyCor(datearr[4], type="length")

    dict_list = [dict1, dict2, dict3, dict4, dict5]
    work_values = getKey(dict_list, "work", type="stand")
    sleep_values = getKey(dict_list, "sleep", type="stand")
    distraction_values = getKey(dict_list, "distractions", type="stand")
    light_values = getKey(dict_list, "light", type="stand")
    inroom_values = getKey(dict_list, "inroom", type="stand")
    print (datearr)

    x_values = ["2023-11-20", "2023-11-21", "2023-11-22", "2023-11-23", "2023-11-24"]

    plt.plot(x_values, work_values, label='work')
    plt.plot(x_values, sleep_values, label='sleep')
    plt.plot(x_values, distraction_values, label='distractions')
    plt.plot(x_values, light_values, label='light')
    plt.plot(x_values, inroom_values, label='in room')

    plt.xlabel('Days')
    plt.ylabel('Amount')
    plt.title('Line Graph with Two Data Series')

    # Adding legend
    plt.legend()

    # Display the plot
    plt.show()

    ### Correlation

    data = {
        "work": work_values,
        "sleep": sleep_values,
        "distractions": distraction_values,
        "light": light_values,
        "inroom": inroom_values
    } 
    print (data)
    df = pd.DataFrame(data)
    corr_matrix = df.corr()
    sn.heatmap(corr_matrix, annot=True)
    plt.show()


def getKey(dicts, key, type="default"):
    # Initialize an array to store values for the key 'work'
    array = []

    # Iterate through each dictionary in the list
    for d in dicts:
        array.append(d[key])

    if type == "stand":
        # Standardise the data
        mean_value = sum(array) / len(array)
        variance = sum((x - mean_value) ** 2 for x in array) / len(array)
        std_dev = variance ** 0.5
        array = [(x - mean_value) / std_dev for x in array]

    if type == "minmax":
        min_val = min(array)
        max_val = max(array)
        array = [(x - min_val) / (max_val - min_val) for x in array]

    return array

# WeekAmounts(["2023-11-27", "2023-11-28", "2023-11-29", "2023-11-30", "2023-12-01"])


### --- Compare the average daily amount of each parameter between before and after the actuation --- ###
def compareWeeksAverage():
    datearr = [
        ["2023-11-20", "2023-11-21", "2023-11-22", "2023-11-23", "2023-11-24"],
        ["2023-11-27", "2023-11-28", "2023-11-29", "2023-11-30", "2023-12-01"]
    ]
    data = []
    for week in datearr:
        dict1 = getDailyCor(week[0], type="length")
        dict2 = getDailyCor(week[1], type="length")
        dict3 = getDailyCor(week[2], type="length")
        dict4 = getDailyCor(week[3], type="length")
        dict5 = getDailyCor(week[4], type="length")

        dict_list = [dict1, dict2, dict3, dict4, dict5]
        work_values = getKey(dict_list, "work")
        sleep_values = getKey(dict_list, "sleep")
        distraction_values = getKey(dict_list, "distractions")
        light_values = getKey(dict_list, "light")
        inroom_values = getKey(dict_list, "inroom")

        weekdata = {
            "work": str(int(sum(work_values) / 5)) + 'h' + str(int((sum(work_values) / 5 - int(sum(work_values) / 5)) * 60)),
            "sleep": str(int(sum(sleep_values) / 5)) + 'h' + str(int((sum(sleep_values) / 5 - int(sum(sleep_values) / 5)) * 60)),
            "distractions": sum(distraction_values) / 5,
            "light": str(int(sum(light_values) / 5)) + 'h' + str(int((sum(light_values) / 5 - int(sum(light_values) / 5)) * 60)),
            "inroom": str(int(sum(inroom_values) / 5)) + 'h' + str(int((sum(inroom_values) / 5 - int(sum(inroom_values) / 5)) * 60))
        }

        data.append(weekdata)
    
    print (data)

# compareWeeksAverage()
