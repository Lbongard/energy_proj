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

##### Import all LMP files and combine into a single DataFrame #####

## First Import RTLMP ##

rt_lmp_df_list = [] # Create a list to store df's


for file in glob.glob("./Data/SP15_interval_LMP/*.csv"):
    
    temp_df = pd.read_csv(file)
    rt_lmp_df_list.append(temp_df)
    

rt_df = pd.concat(rt_lmp_df_list)


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

da_lmp_list = []

for file in glob.glob("./Data/SP15_DA_LMP/*.csv"):
    
    temp_df = pd.read_csv(file)
    da_lmp_list.append(temp_df)

da_df = pd.concat(da_lmp_list)

# Convert starting datetime to datetime type
da_df['INTERVALSTARTTIME_GMT'] = pd.to_datetime(da_df['INTERVALSTARTTIME_GMT'])

da_df = da_df.pivot(index = 'INTERVALSTARTTIME_GMT', columns='LMP_TYPE', values='MW')

# Add prefix to cols for merging later
da_df.columns = ["DA_" + col for col in da_df.columns]



# Join real-time and day-ahead data

df = pd.merge(rt_df, da_df, 
              left_index=True,
              right_index=True)


#### Feature Engineering ####

# Create a variable for weekends
df['friday'] = np.where(df.index.weekday==4, 1, 0)
df['weekend']  = np.where(df.index.weekday>4, 1, 0)

