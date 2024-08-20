from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import mysql.connector
from mpl_toolkits.mplot3d import Axes3D


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

states_strings = ["Pozycja bazowa", "Piłka na prestop", "Piłka na stop", "Piłka na podnośniku",
                  "Piłka na podnośniku - ssawka wysunięta", "Piłka na podnośniku - podniesiona",
                  "Piłka przyssana", "Piłka przyssana - podnośnik w dole",
                  "Piłka przyssana - ssawka wsunięta", "Wydmuch wykonany"]

# Unique states
states = [2 ** num for num in range(len(states_strings) + 1)]

counter = 0
for state in states:
    # Filter data for the current state
    state_data = df[df['state'] == state]

    if state_data.shape[0] == 0:
        counter += 1
        continue

    # Define the features
    features = ['time', 'cumulative_air', 'cumulative_energy']
    X = state_data[features].values

    # Apply KMeans clustering
    kmeans = KMeans(n_clusters=1, random_state=0).fit(X)

    # Get the cluster center
    center = kmeans.cluster_centers_[0]

    # Calculate the distance of each point from the cluster center
    distances = np.linalg.norm(X - center, axis=1)

    # Define a threshold for outliers (e.g., the 75th percentile)
    threshold = np.percentile(distances, 75)

    # Mark outliers
    state_data['distance_from_center'] = distances
    state_data['is_outlier'] = distances > threshold

    # Plot the results
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Plot in-cluster points
    in_cluster = state_data[~state_data['is_outlier']]
    ax.scatter(in_cluster['time'], in_cluster['cumulative_air'], in_cluster['cumulative_energy'],
               s=100, c='green', edgecolors='black', label='In-Cluster')

    # Plot outliers
    outliers = state_data[state_data['is_outlier']]
    ax.scatter(outliers['time'], outliers['cumulative_air'], outliers['cumulative_energy'],
               s=50, c='black', marker='x', label='Outliers')

    # Plot cluster center
    ax.scatter(center[0], center[1], center[2],
               s=300, c='red', edgecolors='black', marker='*', label='Cluster Center')

    ax.set_title(f'KMeans Clustering for State: {states_strings[counter]}')
    ax.set_xlabel('Time[s]')
    ax.set_ylabel('Cumulative Air[l]')
    ax.set_zlabel('Cumulative Energy[Wh]')
    ax.legend()

    plt.savefig(f'charts/{states_strings[counter]}.png')
    counter += 1
