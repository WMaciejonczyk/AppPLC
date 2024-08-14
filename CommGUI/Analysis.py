from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import mysql.connector


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

# Unique states
states = [2 ** num for num in range(11)]

counter = 0
for state in states:
    # Filter data for the current state
    state_data = df[df['state'] == state]

    if state_data.shape[0] == 0:
        counter += 1
        continue

    # Define the features
    features = ['time', 'cumulative_air']
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
    plt.figure(figsize=(12, 8))

    # Plot in-cluster points
    in_cluster = state_data[~state_data['is_outlier']]
    plt.scatter(in_cluster['time'], in_cluster['cumulative_air'],
                s=100, c='green', edgecolors='black', label='In-Cluster')

    # Plot outliers
    outliers = state_data[state_data['is_outlier']]
    plt.scatter(outliers['time'], outliers['cumulative_air'],
                s=50, c='black', marker='x', label='Outliers')

    # Plot cluster center
    plt.scatter(center[0], center[1],
                s=300, c='red', edgecolors='black', marker='*', label='Cluster Center')

    plt.title(f'KMeans Clustering for State: {state}')
    plt.xlabel('Time[s]')
    plt.ylabel('Cumulative Air[l]')
    plt.legend()
    plt.savefig(f'{state}.png')
