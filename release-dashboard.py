# standard library
import os
# dash libs
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.figure_factory as ff
import plotly.graph_objs as go
# pydata stack
import pandas as pd
#import MySQLdb as mdb
import pymysql as mdb
from sqlalchemy import create_engine
from sqlalchemy import exc
import datetime
from datetime import datetime as dt


db_host = ''
db_port = 3306
db_user = ''
db_pass = ''
db_name = ''


def connectToDb(db_host,db_user,db_pass,db_name,db_port):
    try:
        return mdb.connect(db_host,db_user,db_pass,db_name,int(db_port),connect_timeout=10)
    except mdb.Error as e:
        print("Error Connecting To Mysql",e)
        return False

#conn = connectToDb(db_host,db_user,db_pass,db_name,db_port)

engine = create_engine('mysql+mysqldb://%s:%s@%s:%s/%s' % (db_user, db_pass, db_host, db_port, db_name),pool_pre_ping=True)

###########################
# Data Manipulation / Model
###########################

def fetch_data(query):
    #result = pd.read_sql(sql=query,con=conn)
    global engine
    try:
        conn = engine.connect()
        print("Connection Successful")
    except exc.SQLAlchemyError as e:
        print("Error Fetching SQLAlchemy Data",e)
        print("Reconnecting...")
        engine = create_engine('mysql+mysqldb://%s:%s@%s:%s/%s' % (db_user, db_pass, db_host, db_port, db_name))
        conn = engine.connect()

    result = pd.read_sql(sql=query,con=conn)
    return result



def get_comp_names():

    '''Returns the list of component names that are stored in the database'''

    query = "SELECT DISTINCT CompName FROM ReleaseData"
    comps = fetch_data(query)
    comps = list(comps['CompName'].sort_values(ascending=True))
    return comps


def get_sub_comp_names(comp_name):

    '''Returns the list of sub-component names for a component name from the database'''

    query = "SELECT DISTINCT SubCompName FROM ReleaseData WHERE CompName= '%s'" % comp_name
    subComps = fetch_data(query)
    subComps = list(subComps['SubCompName'].sort_values(ascending=True))
    return subComps


def get_release_data(comp_name,sub_comp_name):

    '''Returns release data for the respective compnent and sub-component'''

    query = "SELECT * FROM ReleaseData WHERE CompName='%s' AND SubCompName='%s' ORDER BY ReleaseDate DESC" % (comp_name,sub_comp_name)
    results = fetch_data(query)
    return results


def get_release_data_for_date_range(start_date,end_date):

    '''Returns release data for the date range'''
    start_date = start_date+" 00:00:00"
    end_date = end_date+" 23:59:59"
    query = "SELECT * FROM ReleaseData WHERE ReleaseDate>='%s' AND ReleaseDate<='%s' ORDER BY ReleaseDate DESC" % (start_date,end_date)
    results = fetch_data(query)
    return results


def no_results():
        # Page Header
    result = html.Div([
        html.Br(),
        html.Br(),
        html.H4('No Results Found',style={'textAlign': 'center'})
    ])
    return result


def generate_table(dataframe, max_rows=10):

    '''Given dataframe, return template generated using Dash components'''
    if(dataframe.size == 0):
        return no_results()
    else:
        num = dataframe.ID.size
        s_no = list(range(1, num+1))
        dataframe = dataframe.drop(['ID'], axis=1)
        dataframe.insert(loc=0, column='S.No.', value=s_no)
 
        release_date = ['ReleaseDate']
        hyper_link_col_list = ['SprintLink','ConfluenceLink']
        rows = []
        for i in range(len(dataframe)):
            row = []
            for col in dataframe.columns:
                value = dataframe.iloc[i][col]
                if col in hyper_link_col_list:
                    cell = html.Td(html.A(href=value, target="_blank", children="Link"))
                elif col in release_date:
                    new_date_format = value.strftime("%d-%b-%Y %H:%M:%S")
                    cell = html.Td(children=new_date_format)
                elif col == 'CompName':
                    comp = value
                    cell = html.Td(children=value)
                elif col == 'SubCompName':
                    subcomp = value
                    cell = html.Td(children=value)
                elif (col == 'BuildNum' and comp is not None and subcomp is not None):
                    build_url = 'https://jenkins.ops.company.io/job/'+comp+'/job/'+subcomp+'/job/build/'+str(value)
                    cell = html.Td(html.A(href=build_url, target="_blank", children="#"+str(value)))
                else:
                    cell = html.Td(children=value)
                row.append(cell)
            rows.append(html.Tr(row))

        dataframe.rename(columns={'ReleaseDate':'Release Date', 'CompName':'Component', 'SubCompName':'Sub Component', 'SprintLink':'Sprint Link', 'ConfluenceLink':'Confluence Link', 'ProdPromoter': 'Promoter', 'ReleaseBranch':'Branch', 'BuildNum':'Build No.'}, inplace=True)
        return html.Table(
            # Header
            [html.Tr([html.Th(col) for col in dataframe.columns])] +

#            # Body
             rows,className='responstable'
#            [html.Tr([
#                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
#            ]) for i in range(min(len(dataframe), max_rows))],className='responstable'
        )


def load_comp_names():
    '''Load Component Names'''
    comps = (
        [{'label': comp, 'value': comp}
         for comp in get_comp_names()]
    )
    return comps


def get_header():
    header = html.Div([
        html.Br(),
        html.H1('Production Release Dashboard',style={'textAlign': 'center'})
    ])
    return header


def get_tabs():
    get_tabs = html.Div([
        dcc.Tabs(id="tabs", value='timeline', children=[
                dcc.Tab(label='Release TimeLine', value='timeline'),
                dcc.Tab(label='Release History', value='history'),
            ]),
        html.Div(id='tab-output')
        ])
    return get_tabs


def release_history():
    release_history = html.Div([
        html.Br(),
        html.Div([
            html.Div([
                html.Div([
                    html.Div('Component', className='three columns'),
                    html.Div(dcc.Dropdown(id='component-selector',
                                      options=load_comp_names()),
                             className='nine columns')
                ]),
                html.Div([
                    html.Div('Sub Component', className='three columns'),
                    html.Div(dcc.Dropdown(id='subcomponent-selector'),
                             className='nine columns')
                ]),
            ], className='offset-by-three six columns'),
        html.Div(className='six columns'),
        ], className='row'),
        html.Div([
            html.Div(
                html.Table(id='release-data',style={'margin': '0 auto'}),
                className='twelve columns'
            ),
        ]),
    ])
    return release_history


def release_timeline():
    release_timeline = html.Div([
        dcc.Tabs(id="tabs-timeline", value='quick', children=[
                dcc.Tab(label='Quick Ranges', value='quick'),
                dcc.Tab(label='Time Range', value='duration'),
            ]),
        html.Div(id='tab-output-timeline')
        ], style={
        'width': '80%',
        'fontFamily': 'Sans-Serif',
        'margin-left': 'auto',
        'margin-right': 'auto'
    })
    return release_timeline


def date_picker():
    start_date_temp = datetime.datetime.now() - datetime.timedelta(days = 0)
    end_date_temp = datetime.datetime.now() - datetime.timedelta(days = -1)
    get_date = html.Div([
        dcc.DatePickerRange(
            id='my-date-picker-range',
            initial_visible_month=dt.now(),
            day_size = 30,
            month_format = "MMM, YYYY",
            start_date = start_date_temp.strftime("%Y-%m-%d"),
            end_date = end_date_temp.strftime("%Y-%m-%d"),
	    ),
        ])
    return get_date


def radio_button():
    get_radio_button = html.Div([
         html.Br(),
         dcc.RadioItems(id='quick-value',
         options=[
            {'label': 'Today', 'value': 0},
            {'label': 'Yesterday', 'value': 1},
            {'label': 'Last 2 days', 'value': 2},
            {'label': 'Last 7 days', 'value': 3},
            {'label': 'Last 30 days', 'value': 4},
         ],
         value=0,
         labelStyle={'width': '15%','display': 'inline-block'}
         )
         ])
    return get_radio_button

def get_quick_start_end_date(value):
    os.environ['TZ'] = 'Asia/Kolkata'
    today = datetime.datetime.now() - datetime.timedelta(days = 0)
    today = today.strftime("%Y-%m-%d")
    yesterday = datetime.datetime.now() - datetime.timedelta(days = 1)
    yesterday = yesterday.strftime("%Y-%m-%d")
    last2days = datetime.datetime.now() - datetime.timedelta(days = 2)
    last2days = last2days.strftime("%Y-%m-%d")
    last7days = datetime.datetime.now() - datetime.timedelta(days = 7)
    last7days = last7days.strftime("%Y-%m-%d")
    last30days = datetime.datetime.now() - datetime.timedelta(days = 30)
    last30days = last30days.strftime("%Y-%m-%d")


    if(value == 0):
        start_date = end_date = today
    elif(value == 1):
        start_date = end_date = yesterday
    elif(value == 2):
        start_date = last2days
        end_date = yesterday
    elif(value == 3):
        start_date = last7days
        end_date = yesterday
    elif(value == 4):
        start_date = last30days
        end_date = yesterday
    else:
        start_date = end_date = None

    return start_date,end_date


def time_range():
    get_time_range = html.Div([
        html.Div(date_picker(),className="row",style={'textAlign': 'center'}),
        # Release Data Table
            html.Div(
                html.Table(id='output-container-date-picker-range',style={'margin': '0 auto'}),
                className='twelve columns'),
        ])
    return get_time_range


def quick_ranges():
    get_quick_range = html.Div([
        html.Div(radio_button(),className="row",style={'textAlign': 'center'}),
        # Release Data Table
            html.Div(
                html.Table(id='output-container-quick-ranges',style={'margin': '0 auto'}),
                className='twelve columns'),
        ])
    return get_quick_range


#########################
# Dashboard Layout / View
#########################
# Set up Dashboard and create layout
#app = dash.Dash()

app = dash.Dash(__name__)
server = app.server

app.title = 'Release Dashboard'
app.config['suppress_callback_exceptions']=True

#app.css.config.serve_locally = True
#app.scripts.config.serve_locally = True

app.layout = html.Div([
    get_header(),
    get_tabs(),
])

#############################################
# Interaction Between Components / Controller
#############################################

#History/TimeLine Tab Selector
@app.callback(Output('tab-output', 'children'),
              [Input('tabs', 'value')])
def display_main_tabs(value):
    if value == 'history':
        return release_history()
    elif value == 'timeline':
        return release_timeline()
    else:
        return None

# Load Sub Components in Dropdown
@app.callback(
    Output(component_id='subcomponent-selector', component_property='options'),
    [
        Input(component_id='component-selector', component_property='value')
    ]
)
def populate_subcomponent_selector(comp):

    subcomps = (
        [{'label': subcomp, 'value': subcomp}
         for subcomp in get_sub_comp_names(comp)]
    )
    return subcomps

# Load Database Results
@app.callback(
    Output(component_id='release-data', component_property='children'),
    [
        Input(component_id='component-selector', component_property='value'),
        Input(component_id='subcomponent-selector', component_property='value')
    ]
)
def load_release_data(comp,subcomp):
    if(comp is not None and subcomp is not None):
        results = get_release_data(comp,subcomp)
        return generate_table(results, max_rows=50)

#TimeLine Tab Quick/Time Ranges
@app.callback(Output('tab-output-timeline', 'children'),
              [Input('tabs-timeline', 'value')])
def display_content_timeline(value):
    if value == 'quick':
        return quick_ranges()
    elif value == 'duration':
        return time_range()
    else:
        return None

#Quick Ranges
@app.callback(
    dash.dependencies.Output('output-container-quick-ranges', 'children'),
    [dash.dependencies.Input('quick-value', 'value')])
def all_releases_quick(value):
    start_date,end_date = get_quick_start_end_date(value)
    if(start_date is not None and end_date is not None):
        #print(start_date,end_date)
        results = get_release_data_for_date_range(start_date, end_date)
        return generate_table(results, max_rows=50)

#Time Range
@app.callback(
    dash.dependencies.Output('output-container-date-picker-range', 'children'),
    [dash.dependencies.Input('my-date-picker-range', 'start_date'),
     dash.dependencies.Input('my-date-picker-range', 'end_date')])
def all_releases(start_date,end_date):
    if(start_date is not None and end_date is not None):
        results = get_release_data_for_date_range(start_date, end_date)
        return generate_table(results, max_rows=50)

# start Flask server
if __name__ == '__main__':
    app.run_server(debug=True,host='0.0.0.0',port=8080)
#    app.run_server(debug=False)
