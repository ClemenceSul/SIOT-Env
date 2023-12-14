### IMPORTS 
import dash
from dash import dcc, html
import plotly.express as px
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import pandas as pd

# Data processing function
from dataProcessing import DayData 

### CREATE APP
app = dash.Dash(__name__)

### SET-UP GRAPHS
def create_graphs():
    NbOfDays = 7
    ### (the code commented-out below corresponds to the proper data retreival. 
    ### As I have interrupted my data collection, graphDates has been given some dates for app visualisation purposes.) 
    # # GET A LIST OF DATES 
    # graphDates = []
    # for i in range(0, NbOfDays):
    #     today = datetime.date.today() - datetime.timedelta(days=i)
    
    #     # Get the current date components
    #     year = today.year
    #     month = today.month
    #     day = today.day
    #     # Format the date as a string (optional)
    #     todayDate = f"{year}-{month:02d}-{day:02d}"
    #     graphDates.append(todayDate)
    # graphDates = graphDates[::-1]
    graphDates = ["2023-11-22", "2023-11-23", "2023-11-24", "2023-11-25", "2023-11-26", "2023-11-27", "2023-11-28"]
    print(graphDates)
    
    ### RETREIVE ALL DATA FROM DATA PROCESSING
    mainDatasetLength = 3
    mainDataset = {
        'timestamp': [],
        'luminosity': [],
        'distractions': [],
        'sleep': [],
        'work': [],
    }
    weeklySleep = []
    weeklyProductivity = []
    for index, date in enumerate(graphDates):
        dailyDataset = DayData(date)
        weeklyProductivity.append(dailyDataset['workduration'])
        weeklySleep.append(dailyDataset['sleepduration'])

        if index >= (NbOfDays-mainDatasetLength):
            mainDataset['timestamp'].append(dailyDataset['timestamp'])
            mainDataset['luminosity'].append(dailyDataset['lightDataset'])
            mainDataset['distractions'].append(dailyDataset['disDataset'])
            mainDataset['work'].append(dailyDataset['workDataset'])
                
    mainDataset = {
        'timestamp': [value for day_values in mainDataset['timestamp'] for value in day_values],
        'luminosity': [value for day_values in mainDataset['luminosity'] for value in day_values],
        'distractions': [value for day_values in mainDataset['distractions'] for value in day_values],
        'sleep': [value for day_values in mainDataset['sleep'] for value in day_values],
        'work': [value for day_values in mainDataset['work'] for value in day_values],
    }

    # FIGURE 1 - SHOW THE LIGHT, DISTRACTION & WORK DATA FOR THE PAST 3 DAYS
    figure_pastlife = {
        'data': [
            go.Scatter( # Luminosity
                x=mainDataset['timestamp'],
                y=mainDataset['luminosity'],
                mode='lines',
                name='Luminosity',
                yaxis='y1'
            ),
            go.Scatter( # Distractions
                x=mainDataset['timestamp'],
                y=mainDataset['distractions'],
                mode='lines',
                name='Distractions',
                yaxis='y2',
                line=dict(
                    color='rgb(255, 0, 0)',
                    shape='hv'
                ),
                fill='tozeroy',
                fillcolor='rgba(255, 0, 0, 0.3)'
            ),
            go.Scatter( # Work
                x=mainDataset['timestamp'],
                y=mainDataset['work'],
                mode='lines',
                name='Work',
                yaxis='y3',
                line=dict(
                    color='rgba(0, 0, 0, 0)',
                    shape='hv'
                ),
                fill='tozeroy',
                fillcolor='rgba(117,194,120,0.2)'
            )
        ],
        'layout': go.Layout(
            title='My Past Life',
            xaxis=dict(
                title='Time',
                type='category',
                categoryorder='array',
                showgrid=False,
                dtick=16,
            ),
            yaxis=dict( # Light
                title='Luminosity (lux)', 
                side='left', 
                showgrid=True,
                minallowed='0',
            ),
            yaxis2=dict( #Distractions
                overlaying='y', 
                side='right',
                range=[0.1, 10],
                showgrid=False,
                showline=False,
                showticklabels=False
            ),
            yaxis3=dict( #Work
                overlaying='y', 
                side='right',
                range=[0.1, 0.9],
                showgrid=False,
                showline=False,
                showticklabels=False
            ),
        )
    }

    # FIGURE 2 - SHOW THE PRODUCTIVITY OVER THE PAST 7 DAYS
    figure_productivity = {
        'data': [
            go.Bar( # Productivity
                x=graphDates,
                y=weeklyProductivity,
                marker=dict(
                    color='rgba(117,194,120,0.5)',
                )
            ),
        ],
        'layout': go.Layout(
            title='My Productivity',
            xaxis=dict(
                title='Days',
                type='category',
                showgrid=False,
            ),
            yaxis=dict(
                title='Productivity (hours)', 
                side='left', 
                showgrid=True,
            )
        )
    }

    # FIGURE 2 - SHOW THE SLEEP OVER THE PAST 7 DAYS
    figure_sleep = {
        'data': [
            go.Bar( # Sleep
                x=graphDates,
                y=weeklySleep,
                marker=dict(
                    color='rgba(123,128,238,0.5)',
                )
            ),
        ],
        'layout': go.Layout(
            title='My Sleep',
            xaxis=dict(
                title='Days',
                type='category',
                showgrid=False,
            ),
            yaxis=dict(
                title='Sleep (hours)', 
                side='left', 
                showgrid=True,
            )
        )
    }

    # Return all three figures
    return {
        'pastlife': figure_pastlife,
        'productivity': figure_productivity,
        'sleep': figure_sleep
        }

allgraphs = create_graphs()

# APP LAYOUT
app.layout = html.Div(children=[
    html.H1('IMPACTING MY PRODUCTIVITY'),
    html.H3('(May the light shine on my work!)'),
    # Call the create_graph function to include the graph in the layout
    html.Div(children=[
        dcc.Graph(
            id='line-plot',
            figure=allgraphs['pastlife']
        )
    ], className="graph_box"),
    html.Div(children=[
        html.Div(children=[
            dcc.Graph(
                id='bar-plot',
                figure=allgraphs['productivity']
            )
        ], className="graph_box half_row", id="prod_box"),
        html.Div(children=[
            dcc.Graph(
                id='bar-plot2',
                figure=allgraphs['sleep']
            )
        ], className="graph_box half_row", id="prod_box2"),
    ], className="graph_row")
])

# RUN APP LOCALLY
if __name__ == '__main__':
    app.run_server(debug=False)
    