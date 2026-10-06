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
| M | Mikrofonu aç; konuşmayı bitirince tekrar M ile gönder (en fazla 20 saniye) |
| C | Son altı soru-cevaptan oluşan sohbet geçmişini temizle |
| S | Konuşmayı durdur veya mikrofon kaydını iptal et; analiz sürüyorsa sonucunu yalnızca terminalde göster |
| R | Son başarılı açıklamayı yeniden oku; API isteği göndermez |
| Q / Esc | Kamerayı kapat ve çık |

Sesli okuma sırasında Boşluk ile yeni tarama başlatabilir, R ile son açıklamayı
yeniden okuyabilirsin. Analiz sürerken ikinci API isteği başlatılmaz. S tuşu
API isteğini iptal etmez; o taramanın sesli yanıtını susturur. Yeni taramada
ses yeniden açılır. Hazır, analiz ve hata durumları sesli bildirilir.
Çıkışta ses hemen durdurulur; devam eden ağ isteği tamamlanana kadar süreç
açık kalabilir. Ağ zaman aşımı 30 saniyedir.

## Kamera ve ses ayarları

- Kamera açılamıyorsa Windows kamera izinlerini kontrol et, kamerayı kullanan
  başka uygulamaları kapat veya `.env` içindeki `CAMERA_INDEX=0` değerini `1` yap.
- Türkçe ses sistemde varsa otomatik seçilir. Yoksa Windows dil ayarlarından
  Türkçe konuşma paketini yükle; aksi durumda varsayılan ses kullanılır.
- Ses motoru çalışmazsa açıklama terminale yazılır.
- Ubuntu'da ses için `sudo apt install espeak-ng libespeak1` gerekebilir.

## Veri akışı ve sınırlar

Kamera önizlemesi yereldir. Boşluk ile seçilen kare bulut API'sine gönderilir.
M ile gönderilen soruda ses kaydı ve gönderim anındaki kamera karesi Gemini'ye
birlikte gönderilir; genel sorular da bu akışı kullanır. Mikrofon yalnızca M
ile açılır; S ile iptal edilen kayıt gönderilmez. Ses kaydı diske yazılmaz.
Son altı soru-cevap metni bellekte tutulup takip sorularında yeniden gönderilir;
C tuşuyla temizlenir, uygulama kapanınca silinir. Fotoğraflar uygulama tarafından diske kaydedilmez. Açıklama terminalde
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
açıklamasını kontrol et. Konuşurken S ile durdur, R ile tekrar oku.
Konuşurken Boşluk ile yeniden tara. Analiz sırasında S’ye basıp yanıtın
yalnızca terminale geldiğini kontrol et. Yeni taramada sesin geri geldiğini
doğrula. Konuşurken Q ile kapatıp sesin kesildiğini kontrol et. Kamera ve Türkçe ses
donanım üzerinde ayrıca denenmelidir.

## Sonraki adımlar

1. Ayrı yazı okuma modu.
2. Bekleme modunda yerel görüntü değişikliği algılama.
3. Mobil istemci ve gözlük kamerası bağlantısı.

API uygulaması [Gemini görüntü anlama](https://ai.google.dev/gemini-api/docs/image-understanding)
ve [Interactions API](https://ai.google.dev/api/interactions-api) belgelerini temel alır.

## Sesli sohbeti deneme

Güncellemeden sonra `python -m pip install -r requirements.txt` çalıştır.
Kamera penceresinde M'ye bir kez bas, konuş ve tekrar M'ye basarak gönder.
Mikrofon açılırken mevcut konuşma kesilir; kayıt sırasında asistan konuşmaz.
20 saniyede kayıt otomatik gönderilir. S kaydı iptal eder.

“Masada ne var?” ardından “Rengi ne?” ile görsel takip sorularını;
“Bugün Python çalışmak istiyorum, nereden başlayayım?” ile genel sohbeti dene.
Yanıtı S ile kes, R ile yeniden dinle. C ile konuşma geçmişini temizle.
Windows Ayarlar → Gizlilik ve güvenlik → Mikrofon bölümünde masaüstü
uygulamalarına erişim izni gerekebilir. Gerçek mikrofon, Türkçe ses ve API
uyumluluğu cihazda ayrıca denenmelidir; otomatik testler servisi taklit eder.
