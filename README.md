# Güvenli Belge Anonimleştirme Sistemi

Bu proje, akademik makalelerin yüklenmesi, anonimleştirilmesi, hakemlere yönlendirilmesi ve değerlendirilmesini sağlayan web tabanlı bir sistemdir.  
Amaç, **yazar kimlik bilgilerinin gizlenerek tarafsız hakem değerlendirmesi yapılmasını** sağlamaktır.

## Özellikler
- **Yazar**: PDF makale yükleme, takip numarası alma, revize edilmiş versiyon yükleme, editör ile mesajlaşma.  
- **Editör**: Makale anonimleştirme (yazar adı, kurum, e-posta), görsellerde bulanıklaştırma, hakem atama, log kayıtlarının takibi, değerlendirmeleri yazara iletme.  
- **Hakem**: Anonim makaleleri inceleyip PDF üzerine yorum ekleme ve sisteme yükleme.  
- **Loglama**: Tüm süreç (yükleme, anonimleştirme, hakem atama, değerlendirme, final teslimi) zaman damgalı olarak kayıt altına alınır.  
- **Güvenlik**: AES, RSA, SHA-256 ve Fernet şifreleme yöntemleriyle veri güvenliği sağlanır.  

## Kullanılan Teknolojiler
- **Backend**: Python (Django)  
- **Veritabanı**: SQLite  
- **Frontend**: HTML, CSS (Django template yapısı)  
- **Doğal Dil İşleme (NLP)**: spaCy (kişisel bilgilerin tespiti)  
- **Görsel İşleme**: OpenCV, pytesseract (görsellerde anonimleştirme/bulanıklaştırma)  
- **Şifreleme**: AES, RSA, SHA-256, Fernet  
- **UUID tabanlı takip numarası** ile dosya yönetimi  

## Çalışma Akışı
1. Yazar makalesini PDF olarak yükler → sistem UUID tabanlı takip numarası üretir.  
2. Editör, kişisel bilgileri tespit edip anonimleştirir ve hakeme yönlendirir.  
3. Hakem anonimleştirilmiş PDF üzerinde değerlendirme yapar → sisteme yükler.  
4. Editör, hakem değerlendirmesini yazar bilgileriyle birleştirerek sonucu yazara iletir.  

## Örnek Ekranlar
- Makale yükleme sayfası  
- Editör paneli  
- Hakem değerlendirme ekranı  
- Log kayıtları  

- [Python Fernet Şifreleme](https://onursahin.net/python-ile-veri-sifreleme-ve-cozme-fernet/)  
- [Tesseract OCR Kullanımı](https://www.dusunurlerdergisi.com/post/python-ile-tesseract-ocr-kullan%C4%B1m%C4%B1)  
