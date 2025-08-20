from django.db import models
import uuid

class UzmanlikAlani(models.Model):
    ana_baslik = models.CharField(max_length=100)
    alt_baslik = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.ana_baslik} – {self.alt_baslik}"



from django.utils.text import slugify
from unidecode import unidecode

class Hakem(models.Model):
    ad = models.CharField(max_length=100)
    email = models.EmailField()
    uzmanlik_alanlari = models.ManyToManyField(UzmanlikAlani)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.ad))
        super().save(*args, **kwargs)





class Makale(models.Model):
    takip_numarasi = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField()
    pdf = models.FileField(upload_to='uploads/')
    anonim_pdf = models.FileField(upload_to='uploads/anon/', null=True, blank=True)
    yuklenme_tarihi = models.DateTimeField(auto_now_add=True)
    final_pdf = models.FileField(upload_to='uploads/final/', null=True, blank=True)
    editor_pdf = models.FileField(upload_to='uploads/editor/', null=True, blank=True)
    uzmanlik_alanlari = models.ManyToManyField(UzmanlikAlani, blank=True)
    reviewed_pdf = models.FileField(upload_to='uploads/reviewed/', null=True, blank=True)
    status = models.CharField(max_length=50, default="Beklemede")  


    sifreli_ad = models.TextField(null=True, blank=True)
    sifreli_email = models.TextField(null=True, blank=True)
    sifreli_kurum = models.TextField(null=True, blank=True)



    def __str__(self):
        return f"{self.takip_numarasi} – {self.status}"




class MakaleLog(models.Model):
    makale = models.ForeignKey(Makale, on_delete=models.CASCADE, related_name="loglar")
    islem = models.CharField(max_length=255)
    zaman = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.makale.takip_numarasi} – {self.islem}"




class Mesaj(models.Model):
    makale = models.ForeignKey(Makale, on_delete=models.CASCADE, related_name='mesajlar')
    GONDEREN_SECENEKLERI = (
        ('YAZAR', 'Yazar'),
        ('EDITOR', 'Editör'),
    )
    gonderen = models.CharField(max_length=10, choices=GONDEREN_SECENEKLERI)
    icerik = models.TextField()
    zaman = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.gonderen} – {self.zaman.strftime('%d.%m.%Y %H:%M')}"


class MakaleHakem(models.Model):
    makale = models.ForeignKey(Makale, on_delete=models.CASCADE, related_name="hakem_iliskileri")
    hakem = models.ForeignKey(Hakem, on_delete=models.CASCADE)
    yorum = models.TextField(blank=True, null=True)
    reviewed_pdf = models.FileField(upload_to='uploads/reviewed/', null=True, blank=True)
    durum = models.CharField(max_length=50, choices=[('Atandı', 'Atandı'), ('Değerlendirildi', 'Değerlendirildi')], default='Atandı')

    
    class Meta:
        unique_together = ('makale', 'hakem')

    def __str__(self):
        return f"{self.hakem.ad} - {self.makale.takip_numarasi}"
