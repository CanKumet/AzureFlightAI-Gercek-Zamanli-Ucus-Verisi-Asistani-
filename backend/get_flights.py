# backend/get_flights.py - Basitleştirilmiş versiyon

import os
import json
import pandas as pd
from azure.storage.blob import ContainerClient
from dotenv import load_dotenv

load_dotenv()

# Ortam değişkenlerinden bilgileri al
BLOB_ACCOUNT = os.getenv("BLOB_ACCOUNT")
BLOB_KEY = os.getenv("BLOB_KEY")
BLOB_CONTAINER = os.getenv("BLOB_CONTAINER")


def load_flight_data(max_files=5, max_rows=50):
    print(f"[INFO] load_flight_data başlatıldı - max_files={max_files}, max_rows={max_rows}")

    # Test için örnek veri döndür (Azure bağlantısı yoksa)
    if not BLOB_ACCOUNT or not BLOB_KEY:
        print("[UYARI] Azure bilgileri eksik, test verisi döndürülüyor...")
        return [
            {
                "icao24": "4caa54",
                "callsign": "EAI57KF",
                "origin_country": "Ireland",
                "timestamp": 1756046666,
                "longitude": -3.3631,
                "latitude": 55.9513,
                "altitude": 0,
                "velocity": 8.23
            }
        ]

    try:
        # Azure bağlantısı oluştur
        print(f"[INFO] Azure'a bağlanılıyor... Account: {BLOB_ACCOUNT}")
        connect_str = f"DefaultEndpointsProtocol=https;AccountName={BLOB_ACCOUNT};AccountKey={BLOB_KEY};EndpointSuffix=core.windows.net"
        container = ContainerClient.from_connection_string(connect_str, BLOB_CONTAINER)

        # JSON dosyalarını listele
        print("[INFO] Blob dosyaları listeleniyor...")
        blob_list = list(container.list_blobs(name_starts_with="output/"))
        json_blobs = [b for b in blob_list if b.name.endswith(".json")]

        if not json_blobs:
            print("[UYARI] Hiç JSON dosyası bulunamadı!")
            return []

        json_blobs = sorted(json_blobs, key=lambda x: x.last_modified, reverse=True)[:max_files]
        print(f"[INFO] {len(json_blobs)} dosya işlenecek")

        records = []

        # Her JSON dosyasını işle
        for blob_idx, blob in enumerate(json_blobs):
            print(f"[INFO] {blob_idx + 1}/{len(json_blobs)} - {blob.name} işleniyor...")

            try:
                blob_data = container.download_blob(blob.name).readall()
                text = blob_data.decode("utf-8").strip()

                line_count = len(text.splitlines())
                print(f"[INFO] Dosyada {line_count} satır bulundu")

                for line_num, line in enumerate(text.splitlines()[:max_rows], 1):
                    if not line.strip():
                        continue

                    try:
                        # JSON parsing
                        outer = json.loads(line)

                        if "json_str" not in outer:
                            print(f"[UYARI] Satır {line_num}: json_str alanı yok")
                            continue

                        inner = json.loads(outer["json_str"])

                        if not isinstance(inner, list) or len(inner) < 10:
                            print(f"[UYARI] Satır {line_num}: Geçersiz array format")
                            continue

                        # Veri çıkarma
                        record = {
                            "icao24": str(inner[0]) if inner[0] else "-",
                            "callsign": str(inner[1]).strip() if inner[1] else "-",
                            "origin_country": str(inner[2]) if inner[2] else "-",
                            "timestamp": int(inner[3]) if inner[3] else 0,
                            "longitude": float(inner[5]) if inner[5] is not None else 0.0,
                            "latitude": float(inner[6]) if inner[6] is not None else 0.0,
                            "altitude": float(inner[7]) if inner[7] is not None else 0.0,
                            "velocity": float(inner[9]) if inner[9] is not None else 0.0
                        }

                        records.append(record)

                        if line_num <= 3:  # İlk 3 kaydı göster
                            print(f"[DEBUG] Kayıt {line_num}: {record['callsign']} - {record['origin_country']}")

                    except Exception as line_error:
                        print(f"[HATA] Satır {line_num} işlenemedi: {line_error}")
                        if line_num <= 3:  # İlk 3 hatayı detaylı göster
                            print(f"[DEBUG] Hatalı satır: {line[:100]}...")
                        continue

            except Exception as blob_error:
                print(f"[HATA] {blob.name} dosyası işlenemedi: {blob_error}")
                continue

        print(f"[INFO] Toplam {len(records)} kayıt işlendi")

        if records:
            # İlk kaydı örnek olarak göster
            print(f"[DEBUG] İlk kayıt örneği: {records[0]}")

        return records[:max_rows]

    except Exception as e:
        print(f"[HATA] Ana işlem hatası: {e}")
        import traceback
        traceback.print_exc()
        return []