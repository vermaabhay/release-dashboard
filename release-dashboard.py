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

engine = create_engine('mysql+mysqldb://%s:%s@%s:%s/%s' % (db_user, db_pass, db_host, db_port, db_name))

###########################
# Data Manipulation / Model
###########################

def fetch_data(query):
    #result = pd.read_sql(sql=query,con=conn)
    try:
        conn = engine.connect()
        result = pd.read_sql(sql=query,con=conn)
        return result
    except Error as e:
        print("Error Fetching Data",e)


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

#########################
# Dashboard Layout / View
#########################

def generate_table(dataframe, max_rows=10):

    '''Given dataframe, return template generated using Dash components'''
    if(dataframe.size == 0):
        return None
    else:
        num = dataframe.ID.size
        s_no = list(range(1, num+1))
        dataframe = dataframe.drop(['ID'], axis=1)
        dataframe.insert(loc=0, column='S.No.', value=s_no)

        hyper_link_col_list = ['SprintLink','ConfluenceLink']
        rows = []
        for i in range(len(dataframe)):
            row = []
            for col in dataframe.columns:
                value = dataframe.iloc[i][col]
                if col in hyper_link_col_list:
                    cell = html.Td(html.A(href=value, target="_blank", children="Link"))
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


def onLoad_comp_names():

    '''Actions to perform upon initial page load'''

    comps = (
        [{'label': comp, 'value': comp}
         for comp in get_comp_names()]
    )
    return comps


# Set up Dashboard and create layout
#app = dash.Dash()

app = dash.Dash(__name__)
server = app.server

app.title = 'Release Dashboard'

'''
app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})
'''

app.layout = html.Div([
    # Page Header
    html.Div([
        html.H1('Production Release Dashboard',style={'textAlign': 'center'})
    ]),
    # Dropdown Grid
    html.Div([
        html.Div([
            # Select Component Dropdown
            html.Div([
                html.Div('Component', className='three columns'),
                html.Div(dcc.Dropdown(id='component-selector',
                                      options=onLoad_comp_names()),
                         className='nine columns')
            ]),
            # Select SubComponent Dropdown
            html.Div([
                html.Div('Sub Component', className='three columns'),
                html.Div(dcc.Dropdown(id='subcomponent-selector'),
                         className='nine columns')
            ]),
        ], className='offset-by-three six columns'),
        # Empty
        html.Div(className='six columns'),
        html.Div(className='six columns'),
        html.Div(className='six columns'),
        html.Div(className='six columns'),
        html.Div(className='six columns'),
    ], className='row'),
    # Match Results Grid
    html.Div([
        # Release Data Table
        html.Div(
            html.Table(id='release-data',style={'margin': '0 auto'}),
            className='twelve columns'
        ),
    ]),
])


#############################################
# Interaction Between Components / Controller
#############################################


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
    results = get_release_data(comp,subcomp)
    return generate_table(results, max_rows=50)

# start Flask server
if __name__ == '__main__':
#    app.run_server(debug=True,host='0.0.0.0',port=8080)
    app.run_server(debug=True)
