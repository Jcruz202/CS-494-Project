#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import math
import numpy as np

# Replace this path with the path to your CSV file
csv_file = 'data.csv'

# Read the CSV — it must have columns: chester_x, chester_y, human_x, human_y
df = pd.read_csv(csv_file)

# subtract the first timestamp from every entry
df['time_zeroed'] = df['Timestamp'] - df['Timestamp'].iloc[0]


#Timestamp,Chester_X,Chester_Y,Chester_Theta,Detected_Human_X,Detected_Human_Y,Detected_Distance,Detected_Confidence,True_Distance,Human_X,Human_Y
# Compute Euclidean distance at each row
distances = ((df['Human_X'] - df['Chester_X'])**2 + 
             (df['Human_Y'] - df['Chester_Y'])**2)**0.5

# Plot the distances
plt.figure()
plt.plot(df['time_zeroed'], distances)
plt.xlabel('Time (sec)')
plt.ylabel('Distance (m)')
plt.title('Distance between Chester and Human over Time')
plt.grid(True)
plt.tight_layout()

# Save to a PNG
plt.savefig('distance_plot.png', dpi=300)
plt.clf()

required_col = ["Timestamp","Chester_X","Chester_Y","Chester_Theta","Detected_Human_X","Detected_Human_Y","Detected_Distance","Detected_Confidence","True_Distance","Human_X","Human_Y"]
df_clean = df.dropna(subset=required_col)

c, s = np.cos(df_clean['Chester_Theta']), np.sin(df_clean['Chester_Theta'])

df_clean['adj_chester_x'] = df_clean['Chester_X'] + (
    df_clean['Detected_Human_X'] * c
  - df_clean['Detected_Human_Y'] * s
)

df_clean['adj_chester_y'] = df_clean['Chester_Y'] + (
    df_clean['Detected_Human_X'] * s
  + df_clean['Detected_Human_Y'] * c
)

df_clean['error'] = np.hypot(
    df_clean['adj_chester_x'] - df_clean['Human_X'],
    df_clean['adj_chester_y'] - df_clean['Human_Y']
)

mean_error = df_clean['error'].mean()
rmse       = np.sqrt((df_clean['error']**2).mean())
max_error  = df_clean['error'].max()

print(f"Mean error: {mean_error:.2f} m")
print(f"RMSE      : {rmse:.2f} m")
print(f"Max error : {max_error:.2f} m")


plt.figure()
plt.scatter(df_clean['adj_chester_x'] , df_clean['adj_chester_y'], marker='o', label='Detected Position')
plt.scatter(df_clean['Human_X'] , df_clean['Human_Y'], marker='o', label='Actual Position')
plt.xlabel('X')
plt.ylabel('Y')
plt.title('Actual Human Position vs. Detected Human Position')
plt.legend()
plt.grid(True)
plt.tight_layout()
# Save to a PNG
plt.savefig('detection.png', dpi=300)

# Clear the figure so you can start fresh (or exit without showing)
plt.clf()
