# backend/main.py

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.producer import fetch_flight_data, send_to_eventhub_batch
from backend.ask_llm import ask_llm
from backend.get_flights import load_flight_data  # <-- ✅ Blob'dan veri çekme fonksiyonu

app = FastAPI()

# 🔓 CORS ayarları - Daha geniş izinler
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tüm domainlere izin ver
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 🌐 Frontend klasörünü bağla
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
app.mount("/static", StaticFiles(directory=frontend_path), name="static")


# 🖼️ Dashboard HTML dosyasını sun
@app.get("/dashboard")
def serve_dashboard():
    return FileResponse(os.path.join(frontend_path, "index.html"))


# ✅ API testi için root endpoint
@app.get("/")
def root():
    return {"status": "Flight Analysis API çalışıyor."}


# ✈️ OpenSky'dan veri al → Event Hub'a gönder
@app.post("/send-flight")
def send_flight():
    data = fetch_flight_data()
    if data and data.get("states"):
        send_to_eventhub_batch(data["states"])
        return {"status": "✅ Uçuş verisi Event Hub'a gönderildi."}
    else:
        return {"status": "❌ Veri alınamadı veya boş."}


# 💬 LLM üzerinden doğal dil sorgusu yap - GELİŞTİRİLMİŞ VERSİYON
@app.post("/ask")
async def ask_question(request: Request):
    print("\n" + "=" * 50)
    print("[DEBUG] /ask endpoint çağrıldı")

    try:
        body = await request.json()
        query = body.get("query")

        if not query:
            print("[ERROR] Sorgu eksik!")
            return JSONResponse(
                content={"error": "Sorgu eksik."},
                status_code=400
            )

        print(f"[DEBUG] Kullanıcı sorusu: {query}")

        # LLM'e gerçek verilerle birlikte sor
        print("[DEBUG] ask_llm() fonksiyonu çağrılıyor...")
        cevap = ask_llm(query)

        print(f"[DEBUG] LLM cevabı alındı: {len(cevap)} karakter")
        print("=" * 50 + "\n")

        return JSONResponse(
            content={"response": cevap},
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

    except Exception as e:
        print(f"[ERROR] /ask endpoint hata: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 50 + "\n")

        return JSONResponse(
            content={"error": f"Soru işlenirken hata oluştu: {str(e)}"},
            status_code=500,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )


# OPTIONS pre-flight request için
@app.options("/ask")
def options_ask():
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

# 📥 Azure Blob Storage'tan uçuş verilerini al - DEBUG VERSİYONU
@app.get("/get-flights")
def get_flight_data():
    print("\n" + "=" * 50)
    print("[DEBUG] /get-flights endpoint çağrıldı")
    print("=" * 50)

    try:
        print("[DEBUG] load_flight_data() çağrılıyor...")
        data = load_flight_data()

        print(f"[DEBUG] load_flight_data sonucu:")
        print(f"  - Tip: {type(data)}")
        print(f"  - Uzunluk: {len(data) if hasattr(data, '__len__') else 'N/A'}")

        if data and len(data) > 0:
            print(f"  - İlk kayıt: {data[0]}")
            print(f"[DEBUG] JSONResponse döndürülüyor - {len(data)} kayıt")
        else:
            print(f"[UYARI] Veri boş veya None!")

        # Response'u açıkça belirle
        response_data = data if data else []

        print(f"[DEBUG] Response hazırlandı: {len(response_data)} kayıt")
        print("=" * 50 + "\n")

        return JSONResponse(
            content=response_data,
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

    except Exception as e:
        print(f"[ERROR] get_flight_data hatası: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 50 + "\n")

        return JSONResponse(
            content={"error": f"Veri yüklenirken hata oluştu: {str(e)}"},
            status_code=500,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )


# OPTIONS pre-flight request için
@app.options("/get-flights")
def options_get_flights():
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )