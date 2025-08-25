# backend/ask_llm.py

import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from backend.get_flights import load_flight_data  # Veri yükleme fonksiyonu

# Ortam değişkenlerini yükle
load_dotenv()

# OpenRouter API ayarları
os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")


def analyze_flight_data(query: str, flight_data: list) -> str:
    """
    Uçuş verilerini analiz ederek kullanıcı sorusuna uygun sonuç döndürür
    """
    if not flight_data:
        return "Şu anda analiz edilecek uçuş verisi bulunmuyor."

    # Temel istatistikler hesapla
    total_flights = len(flight_data)

    # Sadece geçerli verileri filtrele
    valid_flights = [f for f in flight_data if f.get('velocity') and f.get('altitude')]

    if not valid_flights:
        return f"Toplam {total_flights} uçuş verisi var ancak analiz için gerekli bilgiler eksik."

    # İstatistikler
    velocities = [f['velocity'] for f in valid_flights if f['velocity'] is not None]
    altitudes = [f['altitude'] for f in valid_flights if f['altitude'] is not None]
    countries = [f['origin_country'] for f in valid_flights if f.get('origin_country')]

    stats = {
        "toplam_ucus": total_flights,
        "gecerli_ucus": len(valid_flights),
        "ortalama_hiz": sum(velocities) / len(velocities) if velocities else 0,
        "maksimum_hiz": max(velocities) if velocities else 0,
        "minimum_hiz": min(velocities) if velocities else 0,
        "ortalama_irtifa": sum(altitudes) / len(altitudes) if altitudes else 0,
        "maksimum_irtifa": max(altitudes) if altitudes else 0,
        "minimum_irtifa": min(altitudes) if altitudes else 0,
        "ulke_sayisi": len(set(countries)) if countries else 0,
        "en_fazla_ulke": max(set(countries), key=countries.count) if countries else "Bilinmiyor"
    }

    return stats


def build_enhanced_prompt(user_query: str, flight_data: list) -> str:
    analysis = analyze_flight_data(user_query, flight_data)

    if isinstance(analysis, str):
        return f"""
Sen bir uçuş verisi analiz asistanısın. Kullanıcının sorusuna mevcut veriler üzerinden cevap ver.

MEVCUT DURUM: {analysis}

Kullanıcı Sorusu: {user_query}

Lütfen bu durumu açıklayarak kullanıcıya bilgi ver.
"""

    # 🔽 SADELEŞTİRİLMİŞ TÜM UÇUŞLARI hazırla
    simplified_data = [
        {
            "callsign": f.get("callsign"),
            "origin_country": f.get("origin_country"),
            "velocity": f.get("velocity"),
            "altitude": f.get("altitude")
        }
        for f in flight_data
        if f.get("velocity") is not None and f.get("altitude") is not None
    ]

    return f"""
Sen bir uçuş verisi analiz asistanısın. Aşağıdaki uçuş verileri üzerinden kullanıcının sorusuna cevap ver.

📊 GÜNCEL İSTATİSTİKLER:
- Toplam uçuş sayısı: {analysis['toplam_ucus']}
- Analiz edilebilir uçuş: {analysis['gecerli_ucus']}
- Ortalama hız: {analysis['ortalama_hiz']:.2f} m/s
- Maksimum hız: {analysis['maksimum_hiz']:.2f} m/s
- Ortalama irtifa: {analysis['ortalama_irtifa']:.2f} m
- Maksimum irtifa: {analysis['maksimum_irtifa']:.2f} m
- Ülke sayısı: {analysis['ulke_sayisi']}
- En çok uçuş yapan ülke: {analysis['en_fazla_ulke']}

📦 TÜM UÇUŞ VERİLERİ:
{json.dumps(simplified_data, indent=2, ensure_ascii=False)}

Kullanıcı Sorusu: {user_query}

Lütfen sadece yukarıdaki verilere dayanarak doğru, kısa ve anlaşılır bir cevap ver.
Varsayım yapma. Sadece veriye dayalı konuş.
"""


def ask_llm(query: str) -> str:
    """
    LLM'e gerçek uçuş verileriyle birlikte soru sor
    """
    try:
        # Önce uçuş verilerini yükle
        print("[DEBUG] LLM için uçuş verileri yükleniyor...")
        flight_data = load_flight_data()

        if not flight_data:
            return "❌ Şu anda analiz edilecek uçuş verisi bulunmuyor. Lütfen önce '/send-flight' endpoint'ini kullanarak veri toplayın."

        print(f"[DEBUG] LLM'e {len(flight_data)} uçuş verisi gönderilecek")

        # LLM'i başlat
        llm = ChatOpenAI(
            model="google/gemma-3-27b-it:free",
            temperature=0.3,
            max_tokens=500,
        )

        # Zenginleştirilmiş prompt ile soru sor
        enhanced_prompt = build_enhanced_prompt(query, flight_data)
        response = llm([HumanMessage(content=enhanced_prompt)])

        result = response.content if hasattr(response, "content") else response.choices[0].message.content

        return f"📊 **Analiz Sonucu** (Toplam {len(flight_data)} uçuş verisi üzerinden):\n\n{result}"

    except Exception as e:
        print(f"[ERROR] LLM isteği hata: {e}")
        return f"❌ [HATA] LLM analizi başarısız oldu: {e}"


# Test için yardımcı fonksiyon
def test_llm_with_data():
    """
    LLM'i test etmek için örnek sorular
    """
    test_queries = [
        "En yüksek irtifada uçan uçak hangisi?",
        "Hangi ülkeden en çok uçuş var?",
        "Ortalama uçuş hızı nedir?",
        "Toplam kaç uçuş verisi var?"
    ]

    print("=== LLM TEST BAŞLADI ===")
    for query in test_queries:
        print(f"\n🔍 Soru: {query}")
        result = ask_llm(query)
        print(f"💡 Cevap: {result}")
    print("\n=== LLM TEST BİTTİ ===")


if __name__ == "__main__":
    # Direkt çalıştırıldığında test yap
    test_llm_with_data()