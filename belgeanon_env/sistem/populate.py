from sistem.models import Hakem, UzmanlikAlani
from django.utils.text import slugify

veriler = [
    ("Yapay Zeka", "Makine Öğrenmesi"),
    ("Yapay Zeka", "Derin Öğrenme"),
    ("Yapay Zeka", "Doğal Dil İşleme"),
    ("Veri Bilimi", "Büyük Veri"),
    ("Veri Bilimi", "Veri Madenciliği"),
    ("Bilgisayar Ağları", "5G ve Ağ Protokolleri"),
    ("Yazılım Mühendisliği", "Agile Yöntemler"),
    ("Gömülü Sistemler", "IoT"),
    ("Siber Güvenlik", "Şifreleme Teknikleri"),
    ("Görüntü İşleme", "Nesne Tanıma"),
    ("Robotik", "Otonom Sistemler"),
    ("Veritabanı Sistemleri", "SQL Optimizasyonu"),
    ("Web Teknolojileri", "Frontend Framework'leri"),
    ("Mobil Uygulama", "Android Geliştirme"),
    ("Mobil Uygulama", "iOS Geliştirme"),

    ("Yapay Zeka", "Duygu Tanıma"),
    ("Yapay Zeka", "LSTM Ağları"),
    ("Biyomedikal", "EEG Sinyal İşleme"),
    ("Sinyal İşleme", "Beyin Dalgası Analizi"),
    ("Yapay Zeka", "Zaman Serisi Tahmini"),

    ("Yapay Zeka", "Affective Computing"),
    ("Yapay Zeka", "CNN"),
    ("Biyomedikal", "EEG"),
    ("Yapay Zeka", "Emotion Recognition"),
    ("Yapay Zeka", "LSTM"),
    ("Veri Bilimi", "DEAP Dataset"),
    ("Veri Bilimi", "SEED Dataset"),
]

alan_dict = {}
for ana, alt in veriler:
    obj, _ = UzmanlikAlani.objects.get_or_create(ana_baslik=ana, alt_baslik=alt)
    alan_dict[f"{ana}-{alt}"] = obj

print("📚 Uzmanlık alanları başarıyla eklendi.")


hakemler = [
    ("Zeynep Yılmaz", "zeynep@example.com", ["Yapay Zeka-Doğal Dil İşleme", "Yapay Zeka-Affective Computing"]),
    ("Emre Kaya", "emre@example.com", ["Veri Bilimi-Veri Madenciliği", "Siber Güvenlik-Şifreleme Teknikleri"]),
    ("Ayşe Demir", "ayse@example.com", ["Yapay Zeka-CNN", "Yapay Zeka-Zaman Serisi Tahmini"]),
    ("Mehmet Can", "mehmet@example.com", ["Biyomedikal-EEG", "Yapay Zeka-LSTM"]),
    ("Derya Aslan", "derya@example.com", ["Yapay Zeka-Emotion Recognition", "Yapay Zeka-Duygu Tanıma"]),
    ("Ahmet Kar", "ahmet@example.com", ["Veri Bilimi-DEAP Dataset", "Veri Bilimi-SEED Dataset"]),
]

for ad, email, alan_kodlari in hakemler:
    slug = slugify(ad)
    hakem, _ = Hakem.objects.get_or_create(ad=ad, email=email, slug=slug)
    for kod in alan_kodlari:
        if kod in alan_dict:
            hakem.uzmanlik_alanlari.add(alan_dict[kod])

print("Hakemler ve uzmanlık alanları başarıyla oluşturuldu.")
