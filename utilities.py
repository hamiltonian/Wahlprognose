import pandas as pd
import numpy as np
from sklearn.neighbors import KernelDensity as KD
from scipy.stats import gaussian_kde as kde
from scipy.stats.mstats import ttest_1samp as ttest
import sqlite3
from collections import defaultdict

pd.set_option("future.no_silent_downcasting", True)

# Get the data
institute = [('allensbach', ['/2002', '/2005', '/2009', '/2013', '/2017', '']),
             ('emnid', ['/{}'.format(j) for j in range(1998, 2009)]+['/2013', '']),
             ('forsa', ['/{}'.format(j) for j in range(1998, 2009)]+['/2013', '']),
             ('politbarometer', ['/stimmung-1998', '/stimmung-2002', '/stimmung-2005', '/stimmung-2009', '/stimmung-2013', '/stimmung-2017', '/stimmung'] ),
             ('gms', ['/stimmung-2005', '/stimmung-2009', '/stimmung-2013', '/stimmung-2017', '/stimmung']),
             ('dimap', ['/{}'.format(j) for j in range(1998, 2009)]+['/2013','']),
             ('insa', ['']),
             ('yougov', [''])]
month_dict = {'Jan. ': '15.01.',
              'Feb. ': '15.02.',
              'Mrz. ': '15.03.',
              'Apr. ': '15.04.',
              'Mai ': '15.05.',
              'Jun. ': '15.06.',
              'Jul. ': '15.07.',
              'Aug. ': '15.08.',
              'Sep. ': '15.09.',
              'Okt. ': '15.10.',
              'Nov. ': '15.11.',
              'Dez. ': '15.12.',
             }
col_dict = defaultdict(lambda: 'Nichtwähler')
col_dict.update({'Datum': 'Datum',
                 'SPD': 'SPD',
                 'Rechte': 'Rechte',
                 **dict.fromkeys(['PIRATEN', 'PIR'], 'PIRATEN'),
                 'AfD': 'AfD',
                 'FW': 'FW',
                 'FDP': 'FDP',
                 'CDU/CSU': 'CDU/CSU',
                 'GRÜNE': 'GRÜNE',
                 'BSW': 'BSW',
                 'Unent- schlossene': 'Unentschlossene',
                 **dict.fromkeys(['PDS', 'Linke.PDS', 'LINKE', 'WASG'], 'LINKE'),
                 **dict.fromkeys(['REP/DVU', 'REP'], 'REP'),
                 **dict.fromkeys(['Nicht- wähler', 'Nichtwähler/ Unentschlos.', 'Nichtwähler/ Unentschl.', 'Nichtw\xc3\xa4hler/Unentschl.'], 'Nichtwähler'),
                 **dict.fromkeys(['Son', 'Sonst.', 'Sonstige'], 'Sonstige'),
                 'Summe': 'Summe',
                 'Befragte': 'Befragte',
                 'Zeitraum': 'Zeitraum'}
                )
nan_dict = {'Datum': np.nan,
            'SPD': '0 %',
            'Rechte': '0 %',
            'PIRATEN': '0 %',
            'AfD': '0 %',
            'FW': '0 %',
            'FDP': '0 %',
            'CDU/CSU': '0 %',
            'GRÜNE': '0 %',
            'Unentschlossene': '0 %',
            'LINKE': '0 %',
            'REP': '0 %',
            'BSW': '0 %',
            'Nichtwähler': '0 %',
            'Sonstige': '0 %',
            'Summe': '0 %',
            'Befragte': 0,
            'Zeitraum': np.nan}
parteien = ['CDU/CSU', #black
            'SPD', #red
            'LINKE', #fuchsia
            'GRÜNE', #limegreen
            'FDP', #yellow
            'AfD', #saddlebrown
            'BSW', #darkmagenta
            'FW', #orange
            'PIRATEN', #darkorange
            'Rechte', #sandybrown
            'REP', #steelblue
            'Sonstige', 
            'Nichtwähler', 
            'Unentschlossene'
            ]
parteien_farben = ['black',
                   'red',
                   'fuchsia', 
                   'limegreen', 
                   'yellow',
                   'saddlebrown', 
                   'darkmagenta',
                   'orange', 
                   'darkorange', 
                   'sandybrown', 
                   'steelblue',
                   'slategrey',
                   'slategrey',
                   'slategrey']
parteien_dict = dict(zip(parteien,parteien_farben))

def get_raw_data(url='https://www.wahlrecht.de/umfragen/', institute=institute):
    raw_data = {}
    cols = []
    # Daten von der Website einlesen
    for i, jahre in institute:
        d = []
        for j in jahre:
            dt = pd.read_html(url + i + j + '.htm')
            if i == 'insa':
                dt = dt[1][:-4]
            else:
                dt = dt[1][:-3]
            dt = dt.replace('Wahl 1998', '27.09.1998')
            dt = dt.replace('Wahl 2002', '22.09.2002')
            dt = dt.replace('Wahl 2005', '18.09.2005')
            dt = dt.replace('Wahl 2009', '27.09.2009')
            dt = dt.replace('Wahl 2013', '22.09.2013')
            dt = dt.replace('Wahl 2017', '24.09.2017')
            dt = dt.replace('Wahl 2021', '26.09.2021')
            dt = dt.replace('??.12.2005', '01.12.2005')
            dt = dt.replace('37,0–38,0 %', '37,5 %')
            dt = dt.replace('32-34 %', '33 %')
            dt = dt.replace('41-43 %', '42 %')
            dt = dt.replace('6-7 %', '6,5 %')
            dt = dt.replace('7-8 %', '7,5 %')
            dt = dt.replace('7,0–8,0 %', '7,5 %')
            dt = dt.replace('38,5–39,5 %', '39 %')
            dt = dt.replace('4,0–4,5 %', '4,25 %')
            dt = dt.replace('6,5–7,5 %', '7 %')
            dt = dt.replace('k. A.','')
            dt.rename(columns={'Unnamed: 0': 'Datum'}, inplace=True)
            try:
                dt['Datum'] = pd.to_datetime(dt['Datum'], format="%d.%m.%Y", exact=False)
            except:
                dt['Datum'] = dt['Datum'].apply(lambda x: month_dict[x[:-4]] + x[-4:] if month_dict.get(x[:-4], None) != None else x)
                dt['Datum'] = pd.to_datetime(dt['Datum'], format="%d.%m.%Y", exact=False)
            dt = dt.filter(regex=r'^(?!.*Unnamed).*$')
            dt.columns = [col_dict[c] for c in dt.columns]
            cols.extend([c for c in dt.columns.values])
            d.append(dt)
        raw_data[i] = d
    cols = list(set(cols))
    
    return raw_data, cols

# Prepare data
def create_survey_and_election_data(raw_data, cols, institute=institute):
    # Bei allen Dataframes die gleichen Spalten erzeugen und alles in einen Dataframe schreiben
    data = pd.DataFrame(columns=cols + ['Institut'])
    data_list = []
    for i, jahre in institute:
        for j,_ in enumerate(jahre):
            dt = raw_data[i][j]
            cols_add = [col for col in cols if col not in dt.columns]
            for col in cols_add:
                dt.loc[:,col] = nan_dict[col]
            dt['Institut'] = i
            dt = dt.loc[:,['Datum'] + parteien + ['Institut']]
            data_list.append(dt)
    data = pd.concat(data_list, ignore_index=True)
    data = data[data['CDU/CSU'] != 'CDU/CSU']
    wahlen = data[data['Datum'].isin(pd.to_datetime(['1998-09-27', '2002-09-22', '2005-09-18', '2009-09-27', '2013-09-22', '2017-09-24', '2021-09-26']))]
    data = data[~data['Datum'].isin(pd.to_datetime(['1998-09-27', '2002-09-22', '2005-09-18', '2009-09-27', '2013-09-22', '2017-09-24', '2021-09-26']))]
    # Zeilen mit NAN bei Datum entfernen
    data = data[~data['Datum'].isnull()]
    data = data[~data['CDU/CSU'].str.contains('telefonischen')]
    data.index = range(len(data))
    for partei in parteien:
        data[partei] = data[partei].fillna('0 %')
        wahlen[partei] = wahlen[partei].fillna('0 %')
        
    sonst = data[data['Sonstige'].str.contains('Son')]['Sonstige']
    for i in sonst.index:
        z = sonst[i].split('%')[:-1]
        for zj in z:
            partei, anteil = zj.split()
            data.loc[i,col_dict[partei]] = anteil + ' %'
            
    sonst_wahlen = wahlen[wahlen['Sonstige'].str.contains('Son')]['Sonstige']
    for i in sonst_wahlen.index:
        z = sonst_wahlen[i].split('%')[:-1]
        for zj in z:
            partei, anteil = zj.split()
            wahlen.loc[i,col_dict[partei]] = anteil + ' %'

    for partei in parteien:
        data[partei] = pd.to_numeric(data[partei].apply(lambda x: str(x)[:-2].replace(',','.')))
        wahlen[partei] = pd.to_numeric(wahlen[partei].apply(lambda x: str(x)[:-2].replace(',','.')))

    data[parteien] = data[parteien].fillna(value=0)
    wahlen[parteien] = wahlen[parteien].fillna(value=0)
    
    # Zeitindizes erstellen
    data_time = data.copy()
    data_time.drop('Datum', inplace=True, axis=1)
    data_time.index = data['Datum']
    data_time.sort_index(inplace=True)

    wahlen_time = wahlen.copy()
    wahlen_time.drop('Datum', inplace=True, axis=1)
    wahlen_time.index = wahlen['Datum']
    wahlen_time.sort_index(inplace=True)
    
    return data_time, wahlen_time

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        #print(sqlite3.version)
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)
        
def insert_sql(conn, sql, *args):
    """
    Create a new project into the projects table
    :param conn:
    :param project:
    :return: project id
    """
    print(args)
    cur = conn.cursor()
    cur.execute(sql, args)
    conn.commit()
    return cur.lastrowid
