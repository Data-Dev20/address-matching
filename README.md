# Courier Clustering & Assignment Application

## Overview

The Courier Clustering & Assignment Application is a powerful Streamlit-based tool designed to optimize delivery logistics. This application helps distribution companies efficiently assign couriers to delivery routes by:

1. Geocoding delivery addresses
2. Clustering nearby locations
3. Intelligently assigning agents to deliveries
4. Optimizing vehicle usage and workload distribution

The system differentiates between heavy deliveries requiring vehicles and normal deliveries, creating an optimal schedule that minimizes delivery days while respecting agent capacity constraints.

## Features

- **Address Processing**: Normalizes and geocodes delivery addresses
- **Spatial Clustering**: Groups nearby deliveries using K-means clustering
- **Agent Assignment**: Assigns agents to deliveries based on:
  - Geographical proximity (cluster-based)
  - Weight constraints (15-30kg for normal deliveries)
  - Vehicle requirements (for packages ≥3kg)
  - Maximum rolls per agent (default: 200)
- **Separate Day Types**: 
  - Vehicle Days (marked with "V" prefix)
  - Normal Days (marked with "N" prefix)
- **Interactive Visualization**: Map-based visualization of delivery clusters
- **Statistics**: Reporting of workload distribution across agents and days
- **Export Capability**: Download assignments as Excel spreadsheet

## How It Works

1. **Upload Data**: Users upload CSV or Excel file containing delivery information
2. **Address Processing**: The system preprocesses and geocodes addresses (latitude/longitude)
3. **Clustering**: Deliveries are clustered based on geographical proximity
4. **Assignment Algorithm**:
   - Heavy deliveries (≥3kg) are assigned to "Vehicle Days"
   - Vehicle availability is tracked across consecutive days
   - Normal deliveries are assigned to maintain 15-30kg workload balance
   - Assignments prioritize completing deliveries in minimum days
5. **Visualization & Export**: Results are displayed on an interactive map and can be exported

## Algorithm Logic

### Vehicle Assignment Logic:
- Deliveries weighing ≥3kg require vehicles
- When a vehicle is assigned to an agent, it remains available for the next day
- The system prioritizes assigning vehicle deliveries to agents who already have vehicles
- Vehicle deliveries are limited by the maximum rolls per agent

### Normal Assignment Logic:
- Normal deliveries (weight <3kg) are tracked separately
- Each agent can handle between 15-30kg per normal day
- If adding a delivery would exceed 30kg, the system finds another agent
- If all agents would exceed limits, the system moves to the next day

## Requirements
- Python 3.7+
- Streamlit
- Pandas
- NumPy
- Scikit-learn
- Plotly
- Geoapify API key (for geocoding)

## Getting Started

1. Install required packages:
   ```
   pip install streamlit pandas numpy scikit-learn plotly requests
   ```

2. Run the application:
   ```
   streamlit run app.py
   ```

3. Input your parameters:
   - Number of agents
   - Maximum rolls per agent
   - Normal weight limits (min/max)
   - Number of clusters

4. Upload your delivery data file and start processing

## Data Format Requirements

The input file should contain columns for:
- Address
- City
- Pincode
- Roll Qty
- Weight (optional, calculated if not provided)

## Created By
Namaskar Distribution Solutions Pvt Ltd | 2025
