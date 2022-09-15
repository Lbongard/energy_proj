# -*- coding: utf-8 -*-
"""
Data import, cleaning, and feature engineering for LMP Data

"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import glob
import os
from datetime import datetime
from functools import reduce

##### Import all LMP files and combine into a single DataFrame #####

# Create function for concatenating multiple csv's into one dataframe

def create_mult_csv_df(filepath):
    """Loops through folder specified in filepath and returns a df that concatenates all csv's in that file"""
    
    # Create list to store df's from each individual df
    temp_df_list = []
    
    # Create path that searches for all csv's in folder
    search_path = filepath + "*csv" 
    
    # Add df's from individual csv's to list
    for file in glob.glob(search_path):
        temp_df = pd.read_csv(file)
        temp_df_list.append(temp_df)
        
    df = pd.concat(temp_df_list) # Combine all df's
    
    return df
    
    

## First Import RTLMP ##    

rt_df = create_mult_csv_df("./Data/SP15_interval_LMP/")

# Convert starting datetime to datetime type
rt_df['INTERVALSTARTTIME_GMT'] = pd.to_datetime(rt_df['INTERVALSTARTTIME_GMT'] )

# The data download from CAISO contains multiple types of prices. Convert from long to wide format
rt_df = rt_df.pivot(index='INTERVALSTARTTIME_GMT', columns='LMP_TYPE', values='VALUE')

# Add prefix to cols for merging later
rt_df.columns = ["RT_" + col for col in rt_df.columns]

# Checking that LMP is roughly equivalent to the sum of all other lmp components at a given time
sum((rt_df['RT_LMP'] - rt_df[['RT_MCC', 'RT_MCE', 'RT_MCL', 'RT_MGHG']].sum(axis=1)) < 0.001) / rt_df.shape[0]

# Create hourly summary to merge wwith DA dataset
hourly_rt_df = rt_df.groupby(rt_df.index.floor("H")).mean()

## Now import DALMP ##

da_df = create_mult_csv_df("./Data/SP15_DA_LMP/")

# Convert starting datetime to datetime type
da_df['INTERVALSTARTTIME_GMT'] = pd.to_datetime(da_df['INTERVALSTARTTIME_GMT'])

da_df = da_df.pivot(index = 'INTERVALSTARTTIME_GMT', columns='LMP_TYPE', values='MW')

# Add prefix to cols for merging later
da_df.columns = ["DA_" + col for col in da_df.columns]



## CAISO Load ##

load_df = create_mult_csv_df("./Data/CAISO_LOAD/")

load_df['INTERVALSTARTTIME_GMT'] = pd.to_datetime(load_df['INTERVALSTARTTIME_GMT'])

# FIltering for only total CAISO load for now
load_df = load_df[load_df['TAC_ZONE_NAME'] == 'Caiso_Totals']

# Getting wide data with import/gen/export as columns
load_df = load_df.pivot(index='INTERVALSTARTTIME_GMT', columns='SCHEDULE', values='MW')

# Create hourly summary to merge wwith DA dataset
hourly_load_df = load_df.groupby(load_df.index.floor("H")).mean()

## Wind and Solar Forecast ##

renew_df = create_mult_csv_df("./Data/Wind_Solar_Forecast/")

renew_df['INTERVALSTARTTIME_GMT'] = pd.to_datetime(renew_df['INTERVALSTARTTIME_GMT'])

# Filtering for just day-ahead and actual generation
keep_vals = ['Renewable Forecast Actual Generation',
             'Renewable Forecast Day Ahead']

renew_df = renew_df[renew_df['LABEL'].isin(keep_vals)]

# Pivoting on hub, renewable type and market

renew_df = renew_df.pivot(index='INTERVALSTARTTIME_GMT', columns=["TRADING_HUB", "RENEWABLE_TYPE", "LABEL"], values="MW")

renew_df.columns = ["_".join(col) for col in renew_df.columns]

# Join real-time and day-ahead data


df_list = [hourly_rt_df, da_df, hourly_load_df, renew_df]
df = reduce(lambda left, right: pd.merge(left, right, 
                                           left_index=True, 
                                           right_index=True), df_list)


#### Feature Engineering ####

# Create a variable for weekends
df['friday'] = np.where(df.index.weekday==4, 1, 0)
df['weekend']  = np.where(df.index.weekday>4, 1, 0)

