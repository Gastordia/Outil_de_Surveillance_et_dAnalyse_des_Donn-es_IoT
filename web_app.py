import streamlit as st
import pandas as pd
import glob
import plotly.graph_objects as go
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import plotly.io as pio
import os

# Page configuration
st.set_page_config(
    page_title="IoT Devices Monitor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom style for metrics
st.markdown("""
    <style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

def load_device_data(device_file):
    try:
        df = pd.read_csv(device_file)
        required_columns = {'timestamp', 'temperature', 'humidity', 'battery_level', 'status'}
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            st.error(f"Missing columns in {device_file}: {', '.join(missing_columns)}")
            return pd.DataFrame()
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df.dropna(subset=['timestamp'], inplace=True)
        cutoff_time = datetime.now() - timedelta(minutes=50)
        df = df[df['timestamp'] > cutoff_time]
        return df
    except:
        return pd.DataFrame()

def get_device_list():
    return sorted(glob.glob('infos-*.csv'))

def display_device_metrics(df, metrics_cols):
    if not df.empty:
        last_reading = df.iloc[-1]
        with metrics_cols[0]:
            st.metric("Temperature", f"{last_reading['temperature']}°C")
        with metrics_cols[1]:
            st.metric("Humidity", f"{last_reading['humidity']}%")
        with metrics_cols[2]:
            st.metric("Battery", f"{last_reading['battery_level']}%")
        with metrics_cols[3]:
            st.metric("Status", last_reading['status'])

def create_charts(df):
    charts = {}
    if not df.empty:
        df_last_10 = df.tail(10)

        # Temperature and Humidity Trends
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df_last_10['timestamp'], y=df_last_10['temperature'], mode='lines', name='Temperature',
                                 line=dict(color='#FF4B4B')))
        fig1.add_trace(go.Scatter(x=df_last_10['timestamp'], y=df_last_10['humidity'], mode='lines', name='Humidity',
                                 line=dict(color='#45B7E8')))
        fig1.update_layout(
            title='Temperature and Humidity Trends',
            xaxis_title='Time',
            yaxis_title='Value',
            height=350,
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=40, r=40, t=40, b=40),
            hovermode="x unified",
            xaxis=dict(showgrid=True, zeroline=False),
            yaxis=dict(showgrid=True, zeroline=False),
            dragmode='zoom',  # Zoom mode enabled
            showlegend=True
        )
        charts['temp_humid'] = fig1

        # Battery and Signal Strength
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df_last_10['timestamp'], y=df_last_10['battery_level'], mode='lines', name='Battery Level',
                                 line=dict(color='#4CAF50')))
        fig2.add_trace(go.Scatter(x=df_last_10['timestamp'], y=df_last_10['signal_strength'], mode='lines', name='Signal Strength',
                                 line=dict(color='#FFA726')))
        fig2.update_layout(
            title='Battery and Signal Strength',
            xaxis_title='Time',
            yaxis_title='Value',
            height=350,
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=40, r=40, t=40, b=40),
            hovermode="x unified",
            xaxis=dict(showgrid=True, zeroline=False),
            yaxis=dict(showgrid=True, zeroline=False),
            dragmode='zoom',  # Zoom mode enabled
            showlegend=True
        )
        charts['battery_signal'] = fig2

        # Pressure Trend (only if 'pressure' column exists)
        if 'pressure' in df.columns:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df_last_10['timestamp'], y=df_last_10['pressure'], mode='lines', name='Pressure',
                                     line=dict(color='#9C27B0')))
            fig3.update_layout(
                title='Pressure Trend',
                xaxis_title='Time',
                yaxis_title='Pressure (hPa)',
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=40, r=40, t=40, b=40),
                hovermode="x unified",
                xaxis=dict(showgrid=True, zeroline=False),
                yaxis=dict(showgrid=True, zeroline=False),
                dragmode='zoom',  # Zoom mode enabled
                showlegend=True
            )
            charts['pressure'] = fig3
    
    return charts

# Function to save plotly figures as images
def save_plot_as_image(fig, file_name):
    img_bytes = pio.to_image(fig, format="png", width=800, height=400)
    with open(file_name, "wb") as f:
        f.write(img_bytes)

# Function to generate PDF without graphs
def generate_pdf(df, device_name, charts):
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 750, f"IoT Device Report: {device_name}")

    # Add table with data
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30, 710, "Device Data:")
    y_position = 690
    c.setFont("Helvetica", 8)
    for index, row in df.iterrows():
        c.drawString(30, y_position, f"{row['timestamp']}, {row['temperature']}°C, {row['humidity']}%, "
                                     f"{row['battery_level']}%, {row['status']}, {row.get('pressure', 'N/A')} hPa")
        y_position -= 12
        # Move to next page if content exceeds page height
        if y_position < 50:
            c.showPage()
            y_position = 750
            c.setFont("Helvetica-Bold", 10)
            c.drawString(30, y_position, "Device Data (continued):")
            y_position -= 20

    # Save PDF to buffer
    c.showPage()
    c.save()

    # Get PDF bytes
    pdf_buffer.seek(0)
    return pdf_buffer

# Function to handle PDF export
def export_pdf(df, device_name, charts):
    pdf_buffer = generate_pdf(df, device_name, charts)
    st.download_button(
        label="Download PDF Report",
        data=pdf_buffer,
        file_name=f"{device_name}_report.pdf",
        mime="application/pdf"
    )

# Function for getting the duration input
def input_duration():
    st.sidebar.title("IoT Devices")
    st.sidebar.markdown("---")

    # Ask for the duration in hours and store it in a file
    duration = st.sidebar.number_input("Enter Time Duration (in hours):", min_value=0, value=0, step=1)
    
    if duration <= 0:
        st.sidebar.warning("Please enter a positive number.")
    else:
        with open("duration.txt", "w") as file:
            file.write(str(duration))  # Save duration to the file
        st.sidebar.success(f"Duration set to {duration} hours! ⏰")

    # If duration has passed, send an email (simplified for now)
    if duration > 0:
        st.sidebar.markdown(f"Timer will expire in {duration} hours.")
        # In real application, you would set up a timer or schedule this to run in the background
        # When time is over, trigger email notification
        # For this example, I'll simulate it:
        try:
            st.experimental_rerun()  # You might use a time-based trigger in actual use case
        except:
            print("")
def main():
    input_duration()  # Call the new input field function for duration input
    
    st.sidebar.markdown("---")
    
    # Load the list of devices
    devices = get_device_list()
    if not devices:
        st.sidebar.warning("No devices detected. Ensure CSV files are in the correct format.")
        return

    # Select a device
    selected_device = st.sidebar.selectbox(
        "Select Device",
        devices,
        format_func=lambda x: f"Device {x.split('-')[1].split('.')[0]}"
    )

    # Display the selected device
    device_name = selected_device.split('-')[1].split('.')[0]
    st.title(f"IoT Device Monitor - {device_name}")

    # Create placeholders for metrics and charts
    metrics_cols = st.columns(4)
    chart_placeholders = [st.empty(), st.empty(), st.empty()]

    # Load and display data
    df = load_device_data(selected_device)
    if not df.empty:
        display_device_metrics(df, metrics_cols)
        charts = create_charts(df)
        for idx, (name, fig) in enumerate(charts.items()):
            chart_placeholders[idx].plotly_chart(fig, use_container_width=True)
        
        # Add Export PDF Button
        export_pdf(df, device_name, charts)

    else:
        st.warning("No data available for this device")

    try:
        if st.button("Refresh Data"):
            st.experimental_rerun()
    except:
        print("")

if __name__ == '__main__':
    main()
