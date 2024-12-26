import smtplib
import os
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from fpdf import FPDF
import time

# Function to create PDF from the last 25 rows of the CSV
def create_pdf_from_csv(csv_file, output_pdf):
    # Read the last 25 rows of the CSV
    df = pd.read_csv(csv_file)
    last_25_rows = df.tail(25)

    # Create a PDF document
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Add title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Last 25 Data Entries", ln=True, align='C')

    # Add table header
    pdf.ln(10)  # Line break
    pdf.set_font("Arial", 'B', 12)
    header = ['Timestamp', 'Temperature (°C)', 'Humidity (%)', 'Battery Level (%)', 'Status', 'Pressure (hPa)']
    for col in header:
        pdf.cell(30, 10, col, border=1, align='C')
    pdf.ln()

    # Add data rows
    pdf.set_font("Arial", size=12)
    for index, row in last_25_rows.iterrows():
        pdf.cell(30, 10, str(row['timestamp']), border=1, align='C')
        pdf.cell(30, 10, str(row['temperature']), border=1, align='C')
        pdf.cell(30, 10, str(row['humidity']), border=1, align='C')
        pdf.cell(30, 10, str(row['battery_level']), border=1, align='C')
        pdf.cell(30, 10, str(row['status']), border=1, align='C')
        pdf.cell(30, 10, str(row['pressure']), border=1, align='C')
        pdf.ln()

    # Save the PDF
    pdf.output(output_pdf)

# Function to send email with the PDF attachment
def send_email(pdf_file):
    # Email configuration (use your own details)
    sender_email = "sender_email@gmai.com"
    receiver_email = "receiver_email@gmail.com"
    subject = "IoT Device Data Report"
    body = "Please find the attached IoT Device Data report."

    # Set up the MIME
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Add the email body
    msg.attach(MIMEText(body, 'plain'))

    # Attach the PDF file
    with open(pdf_file, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(pdf_file)}")
        msg.attach(part)

    # SMTP server (use your email provider's details)
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)  # For Gmail
        server.starttls()
        server.login(sender_email, "password")  # Use an app-specific password if 2FA is enabled
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.close()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")
def get_duration_from_file(file_path="duration.txt"):

    try:
        with open(file_path, "r") as file:
            # Read the content of the file and convert it to an integer
            return int(file.read().strip())
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return None

# Example usage
duration = get_duration_from_file()
if duration is not None:
    print(f"The duration is {duration} hours.")
else:
    print("Could not read the duration from the file.")

# Function to repeatedly send email with PDF every 10 minutes
def email_report_loop():
    while True:
        # Define the CSV and PDF file paths
        csv_file = "your_device_data.csv"  # Replace with your CSV file
        pdf_file = "device_data_report.pdf"

        # Create the PDF from the CSV
        create_pdf_from_csv(csv_file, pdf_file)

        # Send the email with the PDF attached
        duration=get_duration_from_file()
        send_email(pdf_file)

        # Sleep for 10 minutes before the next iteration
        time.sleep(duration*3600)  # 600 seconds = 10 minutes

# Run the loop
if __name__ == "__main__":
    email_report_loop()
