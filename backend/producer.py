import requests
import json
import os
import time
from azure.eventhub import EventHubProducerClient, EventData
from dotenv import load_dotenv

load_dotenv()

EVENT_HUB_CONNECTION_STR = os.getenv("EVENT_HUB_CONNECTION_STR")
EVENT_HUB_NAME = os.getenv("EVENTHUB_NAME")

def fetch_flight_data():
    url = "https://opensky-network.org/api/states/all"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("🛬 Veri alındı.")
            return response.json()  # JSON string değil dict döndürüyoruz
        else:
            print(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"API bağlantı hatası: {e}")
        return None

def send_to_eventhub_batch(states_batch):
    try:
        producer = EventHubProducerClient.from_connection_string(
            conn_str=EVENT_HUB_CONNECTION_STR,
            eventhub_name=EVENT_HUB_NAME
        )
        event_data_batch = producer.create_batch()

        for state in states_batch:
            data = json.dumps(state)
            try:
                event_data_batch.add(EventData(data))
            except ValueError:
                print("⚠️ Mesaj çok büyük, yeni batch ile devam ediliyor.")
                producer.send_batch(event_data_batch)
                event_data_batch = producer.create_batch()
                event_data_batch.add(EventData(data))

        producer.send_batch(event_data_batch)
        producer.close()
        print(f"✅ {len(states_batch)} uçuş verisi Event Hub'a gönderildi.")

    except Exception as e:
        print(f"Event Hub hatası: {e}")

def start_stream(interval_seconds=10):
    print("🔁 Gerçek zamanlı veri akışı başladı...")
    while True:
        try:
            data = fetch_flight_data()
            if data and data.get("states"):
                # Her state = bir uçak
                send_to_eventhub_batch(data["states"])
            else:
                print("⚠️ Veri alınamadı veya boş.")
        except Exception as e:
            print(f"🔻 Genel hata: {e}")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    start_stream(interval_seconds=10)
