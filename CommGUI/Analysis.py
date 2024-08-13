from sklearn.cluster import DBSCAN
from sklearn.datasets import make_blobs
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import mysql.connector
import seaborn as sns

# Step 1: Connect to MySQL database
conn = mysql.connector.connect(
    host=os.getenv('MY_SQL_HOST'),
    user=os.getenv('MY_SQL_USER'),
    password=os.getenv('MY_SQL_PASS'),
    database=os.getenv('MY_SQL_DB')
)

# Query the data
query = "SELECT * FROM states_measurements"
df = pd.read_sql(query, conn)

# Close the connection
conn.close()

label_encoder = LabelEncoder()
df['state_encoded'] = label_encoder.fit_transform(df['state'])

# Prepare the features for clustering
features = df[['state_encoded', 'cumulative_air', 'time']]

# Normalize the features
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features)

# For air consumption
# dbscan = DBSCAN(eps=0.4, min_samples=5)
# For time
dbscan = DBSCAN(eps=0.3, min_samples=5)
# Fit the model
df['cluster'] = dbscan.fit_predict(features_scaled)

# Check cluster labels
# print(df['cluster'].value_counts())
print(df[['state', 'state_encoded', 'cumulative_air', 'time', 'cluster']])

encoded_to_state = {index: state for index, state in enumerate(label_encoder.classes_)}

# Add the state name to the dataframe based on the encoded value
df['state_name'] = df['state_encoded'].map(encoded_to_state)

print(df[['id', 'state', 'cumulative_air', 'time', 'state_encoded', 'cluster', 'state_name']])

all_states = ["Pozycja bazowa", "Piłka na prestop", "Piłka na stop", "Piłka na podnośniku",
              "Piłka na podnośniku - ssawka wysunięta", "Piłka na podnośniku - podniesiona",
              "Piłka przyssana", "Piłka przyssana - podnośnik w dole",
              "Piłka przyssana - ssawka wsunięta", "Wydmuch wykonany"]

state_to_value = {state: i for i, state in enumerate(all_states)}
value_to_state = {v: k for k, v in state_to_value.items()}

df['state_value'] = df['state'].map(state_to_value)

unique_clusters = df['cluster'].unique()
colors = sns.color_palette('tab10', len(unique_clusters) - 1)  # Exclude outliers
color_mapping = {i: colors[i] for i in range(len(colors))}
color_mapping[-1] = 'black'  # Outliers are black

# Plot the data
plt.figure(figsize=(16, 8))

# Plot clusters (excluding outliers) with one marker
sns.scatterplot(data=df[df['cluster'] != -1], x='time', y='cumulative_air', hue='cluster',
                palette=color_mapping, legend='full', s=100)

# Plot outliers with a different marker
sns.scatterplot(data=df[df['cluster'] == -1], x='time', y='cumulative_air',
                color='black', marker='X', legend='full', s=100)

# Customize the plot
# plt.xticks(ticks=list(state_to_value.values()), labels=[value_to_state[v] for v in state_to_value.values()], rotation=45, ha='right')
plt.title('DBSCAN Clustering')
plt.xlabel('Time [s]')
plt.ylabel('Air consumption [l]')
# plt.yscale('log')
plt.tight_layout()
plt.legend(title='Cluster')
plt.show()
