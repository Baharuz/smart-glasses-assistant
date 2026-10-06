# smart-glasses-assistant
Görme engelli bireyler için yapay zeka destekli çevresel algılama ve asistan mobil uygulaması.

İlk geliştirme aşaması: bilgisayar webcam'i üzerinden Türkçe çevre açıklaması
ve sesli okuma prototipi. Mobil uygulama ve gözlük bağlantısı sonraki aşamalardır.

## Kurulum — Windows PowerShell

Python 3.11 veya üzeri ve webcam gerekir. Proje klasöründe çalıştır:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

`.env` içindeki `GEMINI_API_KEY=` satırına [Google AI Studio](https://aistudio.google.com/apikey)
anahtarını yaz. Anahtarı paylaşma; `.env` Git tarafından yok sayılır.
Model erişimi/kota hesabına bağlıdır. İstekler API kullanımına sayılır.

```powershell
.\.venv\Scripts\python.exe -m smart_glasses
```

Kamera penceresi seçiliyken:

| Tuş | İşlem |
| --- | --- |
| Boşluk | Bir kareyi Gemini'ye gönder ve Türkçe açıklamayı oku |
| R | Son başarılı açıklamayı yeniden oku; API isteği göndermez |
| Q / Esc | Kamerayı kapat ve çık |

Analiz veya sesli okuma sürerken yeni istek kabul edilmez. Çıkışta devam eden
işlem tamamlanana kadar süreç açık kalabilir; ağ zaman aşımı 30 saniyedir.

## Kamera ve ses ayarları

- Kamera açılamıyorsa Windows kamera izinlerini kontrol et, kamerayı kullanan
  başka uygulamaları kapat veya `.env` içindeki `CAMERA_INDEX=0` değerini `1` yap.
- Türkçe ses sistemde varsa otomatik seçilir. Yoksa Windows dil ayarlarından
  Türkçe konuşma paketini yükle; aksi durumda varsayılan ses kullanılır.
- Ses motoru çalışmazsa açıklama terminale yazılır.
- Ubuntu'da ses için `sudo apt install espeak-ng libespeak1` gerekebilir.

## Veri akışı ve sınırlar

Kamera önizlemesi yereldir. Yalnızca Boşluk tuşuyla seçilen kare bulut API'sine
gönderilir. Fotoğraflar uygulama tarafından diske kaydedilmez. Açıklama terminalde
gösterilir ve tekrar okuma için bellekte tutulur. İsteklerde `store=false` kullanılır;
bu ayar sağlayıcının genel veri işleme koşullarının yerine geçmez.

Bu bir araştırma prototipidir; açıklamalar hatalı olabilir. Mesafe ölçümü,
güvenli yol yönlendirmesi ve gerçek zamanlı engel uyarısı henüz uygulanmadı.

## Test

API anahtarı ve kamera olmadan servis testleri:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Gerçek cihaz kontrolü: uygulamayı aç, Boşluk ile bir sahneyi tara, ses/terminal
açıklamasını kontrol et, R ile tekrarla ve Q ile kapat. Kamera ve Türkçe ses
donanım üzerinde ayrıca denenmelidir.

## Sonraki adımlar

1. Mikrofonla soru sorma ve görüntüye göre yanıt verme.
2. Bekleme modunda yerel görüntü değişikliği algılama.
3. Mobil istemci ve gözlük kamerası bağlantısı.

API uygulaması [Gemini görüntü anlama](https://ai.google.dev/gemini-api/docs/image-understanding)
ve [Interactions API](https://ai.google.dev/api/interactions-api) belgelerini temel alır.
