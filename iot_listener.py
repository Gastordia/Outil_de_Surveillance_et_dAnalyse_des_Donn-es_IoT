import threading
import time
import random
from datetime import datetime
import queue
import csv
import os

class IoTDevice(threading.Thread):
    def __init__(self, device_id, data_queue, thread_num):
        super().__init__()
        self.device_id = device_id
        self.data_queue = data_queue
        self.running = True
        self.current_data = None
        self.csv_filename = f"infos-{thread_num}.csv"
        self.setup_csv()
    
    def setup_csv(self):
        headers = ['device_id', 'timestamp', 'temperature', 'humidity', 
                  'battery_level', 'signal_strength', 'status', 'pressure']
        if not os.path.exists(self.csv_filename):
            with open(self.csv_filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
    
    def generate_data(self):
        return {
            'device_id': self.device_id,
            'timestamp': datetime.now(),
            'temperature': round(random.uniform(18, 30), 2),
            'humidity': round(random.uniform(30, 80), 2),
            'battery_level': round(random.uniform(20, 100), 2),
            'signal_strength': round(random.uniform(-90, -30), 2),
            'status': random.choice(['active', 'idle', 'error']),
            'pressure': round(random.uniform(980, 1020), 2)
        }

    def __str__(self):
        if not self.current_data:
            return f"IoTDevice {self.device_id} - No data available"
        return (f"IoTDevice {self.device_id}\n"
                f"  Timestamp: {self.current_data['timestamp']}\n"
                f"  Temperature: {self.current_data['temperature']}°C\n"
                f"  Humidity: {self.current_data['humidity']}%\n"
                f"  Battery: {self.current_data['battery_level']}%\n"
                f"  Signal: {self.current_data['signal_strength']} dBm\n"
                f"  Status: {self.current_data['status']}\n"
                f"  Pressure: {self.current_data['pressure']} hPa")

    def run(self):
        while self.running:
            self.current_data = self.generate_data()
            self.data_queue.put(self.current_data)
            
            with open(self.csv_filename, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.current_data.keys())
                writer.writerow(self.current_data)
            
            time.sleep(10)
            print(self)

    def stop(self):
        self.running = False

def data_consumer(data_queue):
    while True:
        data = data_queue.get()
        print(f"Device {data['device_id']} - Temp: {data['temperature']}°C, "
              f"Humidity: {data['humidity']}%, Battery: {data['battery_level']}%")

if __name__ == "__main__":
    data_queue = queue.Queue()
    
    consumer_thread = threading.Thread(target=data_consumer, args=(data_queue,))
    consumer_thread.daemon = True
    consumer_thread.start()
    
    devices = []
    for i in range(3):
        device = IoTDevice(f"DEVICE_{i:03d}", data_queue, i)
        devices.append(device)
        device.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping simulation...")
        for device in devices:
            device.stop()
            device.join()