from dash import Dash, html, dcc, callback, Output, Input, ctx, clientside_callback
import os
import numpy as np
import pandas as pd
from io import StringIO
from scipy.stats import gaussian_kde as kde
from scipy.stats.mstats import ttest_1samp as ttest
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.io as pio
pio.templates.default = "plotly_white"
from plotly_resampler import register_plotly_resampler
from utilities import get_raw_data, create_survey_and_election_data, create_connection, get_data_time, get_wahlen_time
from utilities import parteien, parteien_dict, institute

# Call the register function once and all Figures/FigureWidgets will be wrapped
# according to the register_plotly_resampler its `mode` argument
register_plotly_resampler(mode='auto')

# Incorporate data
#df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder2007.csv')
#raw_data, cols = get_raw_data()
#data_time, wahlen_time = create_survey_and_election_data(raw_data=raw_data, cols=cols)
current_path = os.path.dirname(os.path.abspath(__file__))

# Initialize the app
app = Dash(__name__)
app.title = 'Auswerung der Sonntagsfrage'

# App layout
app.layout = html.Div([
    dcc.Store(id='Aggregierte-Daten', storage_type='session'),
    dcc.Store(id='Aggregierte-Wahlen', storage_type='session'),
    html.Div(children='Wahlprognosen in Deutschland'),
    html.Hr(),
    #dcc.RadioItems(options=['pop', 'lifeExp', 'gdpPercap'], value='lifeExp', id='controls-and-radio-item'),
    #dash_table.DataTable(data=data_time.to_dict('records'), page_size=6),
    html.Div("Wähle Parteien:"),
    dcc.Dropdown(
        id="parteien-dropdown",
        value=parteien[:7],
        options=parteien,
        multi=True,
    ),
    html.Div("Wähle Institute:"),
    dcc.Dropdown(
        id="institute-dropdown",
        value='Mittelwert über alle Institute',
        options=['Mittelwert über alle Institute'] + list(get_data_time()['Institut'].unique()),
        multi=False,
    ),
    html.Div('Wähle Anzahl der Tage, über die gemittelt werden soll:'),
    dcc.Slider(
        id="mean-slider",
        value=14,
        step=1,
        marks={i: str(i) for i in range(1, 61, 1)},
    ),
    html.Div([
    html.Button('Gesamter Verlauf', id='btn-full'),
    html.Button('Letztes Jahr', id='btn-year'),
    html.Button('Letzte 6 Monate', id='btn-6months'),
    html.Button('Letzte 3 Monate', id='btn-3months'),
    html.Button('Seit der letzten Wahl', id='btn-wahl'),
    html.Div(id='container-timestamp'),
    ]),
    
    dcc.Graph(figure={}, id='umfragen-zeitreihe'),
    html.Div('Abweichungen der Institute vom gemeinsamen Mittelwert:'),
    dcc.Graph(figure={}, id='mittelwert-abweichungen'),
])

# Wähle passende Zeiten durch drücken der Knöpfe aus
@callback(
    Output(component_id='Aggregierte-Daten', component_property='data'),
    Output(component_id='Aggregierte-Wahlen', component_property='data'),
    Input(component_id='btn-full', component_property='n_clicks'),
    Input(component_id='btn-year', component_property='n_clicks'),
    Input(component_id='btn-6months', component_property='n_clicks'),
    Input(component_id='btn-3months', component_property='n_clicks'),
    Input(component_id='btn-wahl', component_property='n_clicks'),
    Input(component_id='umfragen-zeitreihe', component_property='relayoutData')
)

def erzeuge_datensatz(btn_full, btn_year,btn_6month,btn_month, btn_wahl,relayout_data):
        # print(relayout_data['xaxis.range[0]'], relayout_data['xaxis.range[1]'])
    data_time = get_data_time()
    wahlen_time = get_wahlen_time()
    end_datum = pd.to_datetime('today').normalize()
    start_datum = end_datum - pd.Timedelta(days=365)
    if "btn-full" == ctx.triggered_id:
        start_datum = data_time.index.min()
    elif "btn-year" == ctx.triggered_id:
        start_datum = end_datum - pd.Timedelta(days=365)
    elif "btn-6months" == ctx.triggered_id:
        start_datum = end_datum - pd.Timedelta(weeks=24)
    elif "btn-3months" == ctx.triggered_id:
        start_datum = end_datum - pd.Timedelta(weeks=12)
    elif "btn-wahl" == ctx.triggered_id:
        start_datum = wahlen_time.index[-1]
    elif relayout_data is not None and 'xaxis.range[0]' in relayout_data.keys():
        start_datum = pd.to_datetime(relayout_data['xaxis.range[0]']).normalize()
        end_datum = pd.to_datetime(relayout_data['xaxis.range[1]']).normalize()
    
    return data_time.loc[start_datum:end_datum].to_json(date_format='iso', orient='split'), wahlen_time.loc[start_datum:end_datum].to_json(date_format='iso', orient='split')
    

# Add controls to build the interaction
@callback(
    Output(component_id='umfragen-zeitreihe', component_property='figure'),
    Input(component_id='Aggregierte-Daten', component_property='data'),
    Input(component_id='Aggregierte-Wahlen', component_property='data'),
    Input(component_id='parteien-dropdown', component_property='value'),
    Input(component_id='institute-dropdown', component_property='value'),
    Input(component_id='mean-slider', component_property='value'),
)

def display_time_series_with_error(agg_data, agg_wahlen, parteien, institut, rolling_mean):
    data = pd.read_json(StringIO(agg_data), orient='split')
    wahlen = pd.read_json(StringIO(agg_wahlen), orient='split')
    if institut == 'Mittelwert über alle Institute':
        mean = data[parteien].rolling(rolling_mean).mean()
        var = data[parteien].rolling(rolling_mean).std()
    else:
        mean = data[parteien + ['Institut']].groupby('Institut').rolling(rolling_mean).mean().loc[institut,:]
        var = data[parteien + ['Institut']].groupby('Institut').rolling(rolling_mean).std().loc[institut,:]
    
    mean.dropna(inplace=True)
    var.dropna(inplace=True)
    
    wahlen = wahlen[wahlen['Institut'] == 'allensbach']
        
    fig = go.Figure()

    for partei in parteien[::-1]:
        fig.add_traces([
            go.Scatter(
                name = partei,
                x=mean.index,
                y=mean[partei],
                line=dict(color=parteien_dict[partei]),
                mode='lines'
            ),
            go.Scatter(
                name= partei + ' + 1 std',
                x=mean.index,
                y=mean[partei] + var[partei],
                mode='lines',
                #marker=dict(color="#444"),
                line=dict(color=parteien_dict[partei],width=0),
                showlegend=False
            ),
            go.Scatter(
                name=partei + ' - 1 std',
                x=mean.index,
                y=mean[partei] - var[partei],
                #marker=dict(color="#444"),
                line=dict(color=parteien_dict[partei],width=0),
                mode='lines',
                #fillcolor='rgba(68, 68, 68, 0.3)',
                fill='tonexty',
                showlegend=False
            ),
            go.Scatter(
                name = partei + ' Wahlergebnis Bundestagswahl',
                x=wahlen.index,
                y=wahlen[partei],
                mode='markers',
                marker_color=parteien_dict[partei],
                marker_size=15,
                marker_line_width=2,
                #marker=dict(size=20,color=parteien_dict[partei], marker_line_width=2),
                showlegend=False
            ),
        ])
    
    
    fig.update_layout(yaxis_range=[mean.min(), mean.max()])
    # fig.update_layout(
    #     xaxis=dict(
    #         rangeslider=dict(
    #             visible=True,
    #         ),
    #         type="date"
    #     )
    # )
    fig.update_layout(
    autosize=False,
    # dragmode='select',
    selectdirection='h',
    xaxis_title="Datum",
    yaxis_title="Prozent",
    #hovermode='x', #'x unified',
    #width=500,
    height=800
    )
    
    return fig
    
@callback(
    Output(component_id='mittelwert-abweichungen', component_property='figure'),
    Input(component_id='Aggregierte-Daten', component_property='data'),
    Input(component_id='parteien-dropdown', component_property='value'),
    Input(component_id='mean-slider', component_property='value'),
    Input(component_id='umfragen-zeitreihe', component_property='figure')
)

def display_mittelwert_abweichungen(agg_data, parteien, rolling_mean, figure_data):
    data = pd.read_json(StringIO(agg_data), orient='split')
    
    mean = data[parteien].rolling(rolling_mean).mean()
    var = data[parteien].rolling(rolling_mean).std()
    
    n_rows = 2
    n_cols = 4
    
    fig = make_subplots(rows=n_rows, cols=n_cols, subplot_titles=[i[0] for i in institute])
    
    for idx,i in enumerate(institute):
        n_row, n_col = divmod(idx,n_cols) 
        
        data_inst = data[data['Institut'] == i[0]]
        data_diff = (data_inst[parteien] - mean.loc[data_inst.index,:])
        
        #p_values[i[0]] = {partei: ttest(data_diff[partei].dropna(), 0)[1] for partei in parteien}
        
        for partei in parteien:
            
            try:
                kde_estimate = kde(data_diff[partei].dropna())
                x = np.linspace(-5,5,500)
                y = kde_estimate.evaluate(x)
            except:
                x = np.linspace(-5,5,500)
                y = np.zeros(len(x))
            
            df = pd.DataFrame({'x': x, 'y':y})
            df['p'] = round(ttest(data_diff[partei].dropna(), 0)[1],4)
            print(df['p'])
                        
            fig.add_trace(
                go.Scatter(
                    name=partei,
                    x=df['x'],
                    y=df['y'],
                    legendgroup=partei,
                    line=dict(color=parteien_dict[partei]),
                    mode='lines',
                    showlegend=(idx==0), # Zeige Legende nur für den ersten Plot
                    customdata=df['p'],
                    hovertemplate = 'p-Wert = %{customdata}'# + str(round(p_values[i[0]][partei],4)),
                ),
                row=n_row+1,
                col=n_col+1,
            )
            
    fig.update_xaxes(range=[-5, 5],
                     title_text='Abweichung vom Mittelwert')
    fig.update_yaxes(title_text='Geschätzte Häufigkeit')
    fig.update_layout(
        #legend_groupclick="toggleitem",
        autosize=False,
        #width=500,
        height=800
    )
    
    return fig

server = app.server

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port='8050', use_reloader=True)
    #app.run_server(debug=True,host='0.0.0.0',port='8050')