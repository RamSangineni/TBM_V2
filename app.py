import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import requests
from io import BytesIO

# Set page configuration
st.set_page_config(
    page_title="TBM Enhancement by AI",
    page_icon="🌍",
    layout="wide"
)

# Custom CSS to improve visual appeal
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        background-color: #4e8df5;
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        border: none;
        width: auto;
        display: inline-block;
    }
    .stButton>button:hover {
        background-color: #3a7bd5;
    }
    .highlight-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .metrics-card {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: center;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Create header layout
col_logo, col_title = st.columns([1, 4])

with col_logo:
    try:
        # Use the logo in the main content area
        response = requests.get("https://www.indianchemicalnews.com/public/uploads/news/2023/07/18177/Welspun_New.jpg", timeout=5)
        if response.status_code == 200:
            logo_small = Image.open(BytesIO(response.content))
            logo_small = logo_small.resize((120, int(120 * logo_small.height / logo_small.width)))
            st.image(logo_small)
    except:
        pass  # Silently fail if logo cannot be loaded

with col_title:
    st.title("TBM Enhancement by AI")

# Create the dataframe with the soil data
data = {
    'Soil Type': [
        'Altered Basalt (A. Basalt)',
        'Basalt mixed with Volcanic Breccia',
        'Compact Basalt + Weathered Basalt',
        'Moderately Weathered Basalt (WB)',
        'Slightly Weathered Basalt (SWBR)',
        'Volcanic Breccia (VB)',
        'Volcanic Tuff (VT)',
        'Weathered Volcanic Breccia (WVB)',
        'Weathered Volcanic Tuff (WVT)'
    ],
    'Thrust Range Min (kN)': [3460, 4656, 3254, 3585, 2999, 3301, 3345, 3432, 3185],
    'Thrust Range Max (kN)': [3839, 4656, 3973, 3585, 3810, 3823, 4390, 3793, 3437],
    'Torque Range Min (kNm)': [427, 352, 372, 439, 460, 371, 497, 369, 272],
    'Torque Range Max (kNm)': [427, 372, 400, 595, 528, 392, 564, 455, 483],
    'Speed Range Min (rpm)': [4.0, 4.24, 3.64, 2.85, 3.03, 3.18, 3.39, 4.11, 3.68],
    'Speed Range Max (rpm)': [4.3, 4.7, 4.55, 4.19, 4.5, 4.43, 3.92, 4.62, 3.91],
    'Soil Group': [
        'Weathered Rock',
        'Mixed Rock',
        'Hard Rock',
        'Weathered Rock',
        'Hard Rock',
        'Breccia',
        'Tuff/Soft Rock',
        'Weathered Breccia',
        'Tuff/Soft Rock'
    ],
    'ROP Range Min (mm/rev)': [6.78, 4.09, 6.06, 7.07, 8.06, 6.78, 4.23, 8.07, 6.38],
    'ROP Range Max (mm/rev)': [6.98, 5.77, 6.94, 7.74, 8.9, 7.54, 6.39, 9.33, 6.53]
}

df = pd.DataFrame(data)

# Calculate ROP Mean for each soil type
df['ROP Mean (mm/rev)'] = (df['ROP Range Min (mm/rev)'] + df['ROP Range Max (mm/rev)']) / 2

# Function to find the best matching soil type
def find_soil_type(thrust, torque, speed):
    # Check if values are in range for any soil type
    matches = []
    
    for index, row in df.iterrows():
        thrust_in_range = (row['Thrust Range Min (kN)'] <= thrust <= row['Thrust Range Max (kN)'])
        torque_in_range = (row['Torque Range Min (kNm)'] <= torque <= row['Torque Range Max (kNm)'])
        speed_in_range = (row['Speed Range Min (rpm)'] <= speed <= row['Speed Range Max (rpm)'])
        
        # Calculate how close the match is (if not in range, how far it is from the range)
        thrust_distance = 0
        torque_distance = 0
        speed_distance = 0
        
        if not thrust_in_range:
            thrust_distance = min(abs(thrust - row['Thrust Range Min (kN)']), abs(thrust - row['Thrust Range Max (kN)']))
        
        if not torque_in_range:
            torque_distance = min(abs(torque - row['Torque Range Min (kNm)']), abs(torque - row['Torque Range Max (kNm)']))
        
        if not speed_in_range:
            speed_distance = min(abs(speed - row['Speed Range Min (rpm)']), abs(speed - row['Speed Range Max (rpm)']))
        
        # Get the range of values to normalize distances
        thrust_range_total = df['Thrust Range Max (kN)'].max() - df['Thrust Range Min (kN)'].min()
        torque_range_total = df['Torque Range Max (kNm)'].max() - df['Torque Range Min (kNm)'].min()
        speed_range_total = df['Speed Range Max (rpm)'].max() - df['Speed Range Min (rpm)'].min()
        
        # Normalize distances by the range of values in the dataset (with check for zero division)
        thrust_norm = thrust_distance / thrust_range_total if thrust_range_total > 0 else 0
        torque_norm = torque_distance / torque_range_total if torque_range_total > 0 else 0
        speed_norm = speed_distance / speed_range_total if speed_range_total > 0 else 0
        
        # Calculate total distance (weighted sum)
        total_distance = thrust_norm + torque_norm + speed_norm
        
        matches.append({
            'index': index,
            'soil_type': row['Soil Type'],
            'rop_mean': row['ROP Mean (mm/rev)'],
            'distance': total_distance,
            'all_in_range': thrust_in_range and torque_in_range and speed_in_range
        })
    
    # Sort matches by whether all values are in range, then by distance
    matches.sort(key=lambda x: (not x['all_in_range'], x['distance']))
    
    return matches[0]  # Return the best match

# Create a nice card for the input fields
with st.container():
    st.markdown('<div class="highlight-card">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Thrust")
        thrust = st.number_input("Enter Thrust", min_value=2500.0, max_value=5000.0, value=None, step=10.0, placeholder="Enter Thrust (kN)")
    
    with col2:
        st.markdown("#### Torque")
        torque = st.number_input("Enter Torque", min_value=250.0, max_value=600.0, value=None, step=5.0, placeholder="Enter Torque (kNm)")
    
    with col3:
        st.markdown("#### Cutter Rpm")
        speed = st.number_input("Enter Cutter rpm", min_value=2.5, max_value=5.0, value=None, step=0.1, placeholder="Enter Speed (rpm)")
    
    # Center-align the button
    # Position the button slightly to the right and more down
    _, spacer_col, button_col, _ = st.columns([1, 0.5, 2, 0.5])
    with button_col:
        # Add more vertical space before the button
        st.write("")
        st.write("")
        st.write("")  # Multiple empty writes add more vertical space
        # Button to predict
        predict_btn = st.button("Soil Type & Optimized Penetration Rate", key="predict_button")

# Display results when the button is clicked
if predict_btn:
    # Check if all values are provided
    if thrust is None or torque is None or speed is None:
        st.error("Please enter values for all three parameters.")
    else:
        best_match = find_soil_type(thrust, torque, speed)
        
        # Create a container for the results
        with st.container():
            st.markdown('<div class="highlight-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="metrics-card">', unsafe_allow_html=True)
                st.metric("Soil Type", best_match['soil_type'])
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metrics-card">', unsafe_allow_html=True)
                st.metric("Penetration Rate", f"{best_match['rop_mean']:.2f} mm/rev")
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
