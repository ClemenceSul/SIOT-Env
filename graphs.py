import pandas as pd
from dataProcessing import DayData
import seaborn as sn
import matplotlib.pyplot as plt

def getDailyCor(date, type="default"):
    data = DayData(date)

    if type == "default":
        del data['timestamp']
        del data['workduration']
        df = pd.DataFrame(data)
        corr_matrix = df.corr()
        return corr_matrix
    elif type == "length":
        del data['timestamp']
        


def OneDay(date):
    corr_matrix = getDailyCor(date)
    sn.heatmap(corr_matrix, annot=True)
    plt.show()

# OneDay("2023-11-20")

def WeekAverage(datearr):
    week_corr = (getDailyCor(datearr[0]) + getDailyCor(datearr[1]) + getDailyCor(datearr[2]) + getDailyCor(datearr[3]) + getDailyCor(datearr[4])) / 5
    sn.heatmap(week_corr, annot=True)
    plt.show()

# WeekAverage(["2023-11-20", "2023-11-21", "2023-11-22", "2023-11-23", "2023-11-24"])

def WeekendAverage(datearr):
    weekend_corr = (getDailyCor(datearr[0]) + getDailyCor(datearr[1])) / 2
    sn.heatmap(weekend_corr, annot=True)
    plt.show()

WeekendAverage(["2023-11-25", "2023-11-26"])

def WeekAmounts(datearr):
    print ("hi")

WeekAmounts(["2023-11-20", "2023-11-21", "2023-11-22", "2023-11-23", "2023-11-24"])