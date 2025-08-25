// 🔍 Soru sorulduğunda LLM'e gönder - İyileştirilmiş
async function askQuestion() {
    const query = document.getElementById("userQuery").value.trim();
    const responseDiv = document.getElementById("response");
    const askButton = document.querySelector("button[onclick='askQuestion()']");

    if (!query) {
        responseDiv.innerHTML = `
            <div style="color: #e74c3c;">
                ❌ Lütfen bir soru yazın.
            </div>
        `;
        return;
    }

    // Button'u deaktif et ve loading göster
    askButton.disabled = true;
    askButton.innerHTML = "🤔 Düşünüyor...";

    responseDiv.innerHTML = `
        <div style="color: #3498db;">
            <span class="status-indicator status-loading"></span>
            AI analiz yapıyor, lütfen bekleyin...
        </div>
    `;

    try {
        console.log("AI'ya soru gönderiliyor:", query);

        const response = await fetch("http://127.0.0.1:8000/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({ query }),
            mode: 'cors'
        });

        if (!response.ok) {
            throw new Error(`HTTP Error: ${response.status}`);
        }

        const data = await response.json();
        console.log("AI yanıtı alındı:", data);

        if (data.response) {
            // Markdown-style formatlamayı basit HTML'e çevir
            let formattedResponse = data.response
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // **bold**
                .replace(/\*(.*?)\*/g, '<em>$1</em>')              // *italic*
                .replace(/\n\n/g, '</p><p>')                       // Paragraflar
                .replace(/\n/g, '<br>');                           // Satır sonları

            responseDiv.innerHTML = `
                <div style="color: #27ae60;">
                    <span class="status-indicator status-success"></span>
                    <strong>AI Analiz Sonucu:</strong>
                </div>
                <div style="margin-top: 10px; line-height: 1.6;">
                    <p>${formattedResponse}</p>
                </div>
            `;
        } else if (data.error) {
            responseDiv.innerHTML = `
                <div style="color: #e74c3c;">
                    <span class="status-indicator status-error"></span>
                    <strong>Hata:</strong> ${data.error}
                </div>
            `;
        } else {
            responseDiv.innerHTML = `
                <div style="color: #e74c3c;">
                    <span class="status-indicator status-error"></span>
                    Bilinmeyen hata oluştu.
                </div>
            `;
        }
    } catch (err) {
        console.error("AI isteği hatası:", err);
        responseDiv.innerHTML = `
            <div style="color: #e74c3c;">
                <span class="status-indicator status-error"></span>
                <strong>Bağlantı Hatası:</strong> FastAPI sunucusu çalışıyor mu?<br>
                <small>Detay: ${err.message}</small>
            </div>
        `;
    } finally {
        // Button'u tekrar aktif et
        askButton.disabled = false;
        askButton.innerHTML = "🔍 Sor";
    }
}

// 📊 Uçuş verilerini çekip tabloya ekle - Önceki kod aynı
async function loadFlightData() {
    const loadingDiv = document.getElementById("loading");
    const errorDiv = document.getElementById("error");
    const tableDiv = document.getElementById("flightTable");

    try {
        // Loading durumunu göster
        loadingDiv.style.display = "block";
        errorDiv.style.display = "none";

        console.log("Uçuş verileri yükleniyor...");
        console.log("Fetch URL:", "http://127.0.0.1:8000/get-flights");

        const response = await fetch("http://127.0.0.1:8000/get-flights", {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            mode: 'cors'
        });

        if (!response.ok) {
            throw new Error(`HTTP Error: ${response.status}`);
        }

        const result = await response.json();
        console.log("API yanıtı:", result);

        // Hata kontrolü
        if (result.error) {
            throw new Error(result.error);
        }

        // Veri kontrolü
        if (!Array.isArray(result) || result.length === 0) {
            throw new Error("Veri bulunamadı veya yanlış formatta");
        }

        const flights = result;
        const tbody = document.getElementById("flightData");
        tbody.innerHTML = ""; // Eski verileri temizle

        console.log(`${flights.length} uçuş verisi işleniyor...`);

        flights.forEach((flight, index) => {
            const row = document.createElement("tr");

            const fields = [
                "callsign",
                "icao24",
                "origin_country",
                "velocity",
                "altitude",
                "latitude",
                "longitude",
                "timestamp"
            ];

            fields.forEach(field => {
                const cell = document.createElement("td");
                let value = flight[field];

                // Değer kontrolü ve formatlaması
                if (value === null || value === undefined || value === "") {
                    value = "-";
                } else if (field === "timestamp" && value !== "-") {
                    // Unix timestamp'i tarih formatına çevir
                    const date = new Date(value * 1000);
                    value = date.toLocaleString('tr-TR');
                } else if (["velocity", "altitude", "latitude", "longitude"].includes(field) && value !== "-") {
                    // Sayısal değerleri formatla
                    value = parseFloat(value).toFixed(2);
                }

                cell.textContent = value;
                row.appendChild(cell);
            });

            tbody.appendChild(row);
        });

        // Başarılı yükleme
        loadingDiv.style.display = "none";
        tableDiv.style.display = "table";
        console.log("Veriler başarıyla yüklendi");

    } catch (err) {
        console.error("Uçuş verileri alınırken hata oluştu:", err);

        // Hata durumunu göster
        loadingDiv.style.display = "none";
        errorDiv.style.display = "block";
        errorDiv.textContent = `Hata: ${err.message}`;
        tableDiv.style.display = "none";
    }
}

// 🔄 Verileri yenile butonu
async function refreshData() {
    console.log("Veriler yenileniyor...");
    const refreshButton = document.querySelector("button[onclick='refreshData()']");

    // Button'u deaktif et
    refreshButton.disabled = true;
    refreshButton.innerHTML = "🔄 Yenileniyor...";

    try {
        await loadFlightData();
    } finally {
        // Button'u tekrar aktif et
        refreshButton.disabled = false;
        refreshButton.innerHTML = "🔄 Verileri Yenile";
    }
}

// 🚀 Sayfa yüklenince verileri getir
window.addEventListener("DOMContentLoaded", () => {
    console.log("Sayfa yüklendi, veriler alınıyor...");
    loadFlightData();
});

// 📝 Enter tuşu ile soru sorma
document.addEventListener("DOMContentLoaded", () => {
    const textarea = document.getElementById("userQuery");
    if (textarea) {
        textarea.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                askQuestion();
            }
        });
    }
});

// 🎯 Örnek sorular ekleme
function addSampleQuestions() {
    const sampleQuestions = [
        "En yüksek irtifada uçan uçak hangisi?",
        "Hangi ülkeden en çok uçuş var?",
        "Ortalama uçuş hızı nedir?",
        "Toplam kaç uçuş verisi var?",
        "En hızlı uçan uçağın bilgilerini ver",
        "Türkiye'den kaç uçuş var?"
    ];

    const questionsDiv = document.createElement("div");
    questionsDiv.innerHTML = `
        <div style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
            <strong>💡 Örnek Sorular:</strong><br>
            ${sampleQuestions.map(q => 
                `<button style="margin: 2px; padding: 5px 10px; font-size: 12px; background: #ecf0f1; border: 1px solid #bdc3c7;" 
                 onclick="document.getElementById('userQuery').value='${q}'">${q}</button>`
            ).join('')}
        </div>
    `;

    const questionSection = document.querySelector(".question-section");
    if (questionSection && !document.querySelector(".sample-questions")) {
        questionsDiv.className = "sample-questions";
        questionSection.appendChild(questionsDiv);
    }
}

// Sayfa yüklendiğinde örnek soruları ekle
window.addEventListener("DOMContentLoaded", () => {
    setTimeout(addSampleQuestions, 1000); // 1 saniye bekle
});