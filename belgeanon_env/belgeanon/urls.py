
from django.contrib import admin
from django.urls import path
from sistem.views import makale_yukle
from django.conf import settings
from django.conf.urls.static import static
from sistem.views import (
    makale_yukle,
    makale_durumu,
    editor_panel,
    anonimlestir,
    anahtar_kelimeleri_goster,
    anonim_makaleler_paneli,
    hakem_atama,
    hakem_oner,
    hakem_paneli,
    makale_degerlendir,
    final_pdf_yukle,
    log_kaydi_goster,
    mesaj_paneli,
    anahtar_kelime_json,
    tum_log_kaydi,
    anasayfa,
    hakem_giris,
    editor_mesaj_paneli,
    deanonimlestir,
)


urlpatterns = [
    path('', anasayfa, name='anasayfa'),
    path('hakem-giris/', hakem_giris, name='hakem_giris'),
    #path('admin/', admin.site.urls),
    #path('', makale_yukle, name='makale_yukle'),
    path('makale-yukle', makale_yukle, name='makale_yukle'),
    path('makale-durumu/', makale_durumu, name='makale_durumu'),
    path('editor-paneli/', editor_panel, name='editor_paneli'),
    path("mesaj-paneli/<uuid:takip_no>/", mesaj_paneli, name="mesaj_paneli"),
    path('anonimlestir/<uuid:takip_no>/', anonimlestir, name='anonimlestir'),
    path('anahtar-kelimeler/<uuid:takip_no>/', anahtar_kelimeleri_goster, name='anahtar_kelime'),
    path('anahtar-kelimeler-json/<str:takip_no>/', anahtar_kelime_json, name='anahtar_kelime_json'),
    path('anonim-makaleler/', anonim_makaleler_paneli, name='anonim_makaleler_paneli'),
    path('anonim-panel/', anonim_makaleler_paneli, name='anonim_makaleler'),
    path('hakem-atama/<uuid:takip_no>/', hakem_atama, name='hakem_atama'),
    path('hakem-oner/<uuid:takip_no>/', hakem_oner, name='hakem_oner'),
    path('hakem/<slug:slug>/', hakem_paneli, name='hakem_paneli'),
    path('degerlendir/<uuid:takip_no>/<slug:slug>/', makale_degerlendir, name='makale_degerlendir'),
    path('final-pdf/<uuid:takip_no>/', final_pdf_yukle, name='final_pdf_yukle'),
    path('loglar/<uuid:takip_no>/', log_kaydi_goster, name='log_kaydi'),
    path('tum-loglar/', tum_log_kaydi, name='tum_log_kaydi'),
    #path('mesajlar/<uuid:takip_no>/', mesaj_paneli, name='mesaj_paneli'),
    path('editor/mesaj/<uuid:takip_no>/', editor_mesaj_paneli, name='editor_mesaj'),
    path('deanonimlestir/<uuid:takip_no>/', deanonimlestir, name='deanonimlestir'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



