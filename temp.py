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

##### Import all files and combine into a single DataFrame #####

lmp_df_list = [] # Create a list to store df's


for file in glob.glob("./Data/CAISO_interval_LMP/*.csv"):
    
    temp_df = pd.read_csv(file)
    lmp_df_list.append(temp_df)
    


df = pd.concat(lmp_df_list)

# Convert all column names to lower, continuous names

for colname in df.columns:
    new_name = "_".join(word for word in colname.split()).lower()
    df.rename({colname:new_name}, inplace=True, axis=1)

df.columns

# Convert starting datetime to datetime type
df['intervalstarttime_gmt'] = pd.to_datetime(df['intervalstarttime_gmt'] )

# The data download from CAISO contains multiple types of prices. Convert from long to wide format
df = df.pivot(index='intervalstarttime_gmt', columns='lmp_type', values='value')

# Checking that LMP is roughly equivalent to the sum of all other lmp components at a given time
sum((df['LMP'] - df[['MCC', 'MCE', 'MCL', 'MGHG']].sum(axis=1)) < 0.001) / df.shape[0]

fig, ax = plt.subplots()

#plt.plot(df["2022-08-05":"2022-08-20"]['LMP'])

ax.plot(df.index, df['LMP'])

ax.set_xticks(df.index)

ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
ax.xaxis.set_minor_formatter(mdates.DateFormatter("%Y-%m"))
_ = plt.xticks(rotation=90)    

