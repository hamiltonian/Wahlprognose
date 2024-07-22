#!/usr/bin/env python


import pandas as pd
from utilities import get_raw_data, create_survey_and_election_data, create_connection
import logging
logging.basicConfig(level=logging.INFO)

# Defining main function 
def main():
    logger = logging.getLogger('main: ')
    logger.info('Reading Data from source...')
    raw_data, cols = get_raw_data()
    data_time, wahlen_time = create_survey_and_election_data(raw_data=raw_data, cols=cols)
    logger.info('...done')
    
    logger.info('Creating DB connection...')
    conn = create_connection('data/wahlprognosen.db')
    logger.info('...done')
    
    logger.info('Writing tables to DB...')
    data_time.to_sql('Prognosen', conn, if_exists='replace')
    wahlen_time.to_sql('Wahlen', conn, if_exists='replace')
    logger.info('...done')
    logger.info('Goodbye!')
  
# Using the special variable  
# __name__ 
if __name__=="__main__": 
    main() 
