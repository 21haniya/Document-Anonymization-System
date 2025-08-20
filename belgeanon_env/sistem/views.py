from django.shortcuts import render, redirect, get_object_or_404
from .forms import MakaleForm, MesajForm
from .models import Makale, Hakem, MakaleLog, MakaleHakem
from .utils import create_anonymized_pdf, extract_keywords_from_pdf, tahmin_et_uzmanlik_alanlari, log_ekle, sifrele, desifrele, anonymize_text_by_type_with_fallback
from django.http import HttpResponse
import os
from django.core.files import File
from django.urls import reverse



def anasayfa(request):
    return render(request, 'anasayfa.html')

def hakem_giris(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        hakem = get_object_or_404(Hakem, email=email)
        return redirect('hakem_paneli', slug=hakem.slug)
    return redirect('anasayfa')



def makale_yukle(request):
    takip_numarasi = None
    if request.method == 'POST':
        form = MakaleForm(request.POST, request.FILES)
        if form.is_valid():
            makale = form.save()
            log_ekle(makale, "Makale yüklendi.")
            takip_numarasi = makale.takip_numarasi
    else:
        form = MakaleForm()

    return render(request, 'makale_yukle.html', {'form': form, 'takip_numarasi': takip_numarasi})




from django.shortcuts import render, get_object_or_404
from .models import Makale
from .forms import MesajForm

def makale_durumu(request):
    takip_no = request.GET.get('takip')
    makale = None
    mesajlar = []
    form = MesajForm()
    sorgulandi = False

    if takip_no:
        sorgulandi = True
        try:
            makale = Makale.objects.get(takip_numarasi=takip_no)
            mesajlar = makale.mesajlar.order_by("zaman")

            if request.method == 'POST':
                form = MesajForm(request.POST)
                if form.is_valid():
                    mesaj = form.save(commit=False)
                    mesaj.makale = makale
                    mesaj.gonderen = 'YAZAR'
                    mesaj.save()
                    form = MesajForm()  
        except Makale.DoesNotExist:
            makale = None

    return render(request, 'makale_durumu.html', {
        'makale': makale,
        'mesajlar': mesajlar,
        'form': form,
        'sorgulandi': sorgulandi,
    })




def editor_panel(request):
    makaleler = Makale.objects.all().order_by('-yuklenme_tarihi')

    for makale in makaleler:
        if makale.uzmanlik_alanlari.count() == 0:
            try:
                pdf_path = makale.pdf.path
                keywords = extract_keywords_from_pdf(pdf_path)
                if not keywords:
                    keywords = extract_keywords_from_pdf_with_ocr(pdf_path)

                alanlar = tahmin_et_uzmanlik_alanlari(keywords, esik=0.7)

                for alan in alanlar:
                    makale.uzmanlik_alanlari.add(alan)

            except Exception as e:
                print(f"{makale.takip_numarasi} için hata:", e)

       
        makale.benzersiz_ana_basliklar = list(set([alan.ana_baslik for alan in makale.uzmanlik_alanlari.all()]))

    return render(request, 'editor_panel.html', {'makaleler': makaleler})



def anonimlestir(request, takip_no):
    try:
        makale = Makale.objects.get(takip_numarasi=takip_no)
        pdf_path = makale.pdf.path
    except Makale.DoesNotExist:
        return JsonResponse({'success': False})

    if request.method == 'POST':
        secilen_turler = request.POST.getlist("turlar")  # ['PERSON', 'ORG', 'EMAIL']
        secilecek_veriler = anonymize_text_by_type_with_fallback(pdf_path, secilen_turler)


        import json

        adlar = []
        emailler = []
        kurumlar = []

        for veri in secilecek_veriler:
            if isinstance(veri, dict):
                if veri['label'] == 'PERSON':
                    adlar.append(sifrele(veri['text']))
                elif veri['label'] == 'EMAIL':
                    emailler.append(sifrele(veri['text']))
                elif veri['label'] == 'ORG':
                    kurumlar.append(sifrele(veri['text']))

        makale.sifreli_ad = json.dumps(adlar)
        makale.sifreli_email = json.dumps(emailler)
        makale.sifreli_kurum = json.dumps(kurumlar)



        makale.save()

        keywords = extract_keywords_from_pdf(pdf_path)
        if not keywords:
            keywords = extract_keywords_from_pdf_with_ocr(pdf_path)
        alanlar = tahmin_et_uzmanlik_alanlari(keywords)
        for alan in alanlar:
            makale.uzmanlik_alanlari.add(alan)

        anonim_pdf_path = create_anonymized_pdf(pdf_path, secilecek_veriler, takip_no)

        relative_path = anonim_pdf_path.lstrip("/")  # 'media/uploads/anon/...'
        

        with open(relative_path, "rb") as f:
            makale.anonim_pdf.save(f"{takip_no}_anon.pdf", File(f), save=True)
            makale.editor_pdf.save(f"{takip_no}_editor.pdf", File(f), save=True)
            log_ekle(makale, "Makale editör tarafından anonimleştirildi.")

    
        return JsonResponse({
            'success': True,
            'download_url': f'/{relative_path}'
        })


    return render(request, 'anonimlestir.html', {'makale': makale})






def anahtar_kelimeleri_goster(request, takip_no):
    try:
        makale = Makale.objects.get(takip_numarasi=takip_no)
        pdf_path = makale.pdf.path
        keywords = extract_keywords_from_pdf(pdf_path)
        if not keywords:
            keywords = extract_keywords_from_pdf_with_ocr(pdf_path)

    except Exception as e:
        print("Hata oluştu:", e)
        keywords = []

    return render(request, 'anahtar_kelimeler.html', {
        'keywords': keywords,
        'makale': makale
    })



from django.http import JsonResponse

def anahtar_kelime_json(request, takip_no):
    try:
        makale = Makale.objects.get(takip_numarasi=takip_no)
        pdf_path = makale.pdf.path
        keywords = extract_keywords_from_pdf(pdf_path)
        if not keywords:
            keywords = extract_keywords_from_pdf_with_ocr(pdf_path)
    except Exception as e:
        print("JSON hata:", e)
        keywords = []

    return JsonResponse({'keywords': keywords})






def anonim_makaleler_paneli(request):
    anonim_makaleler = Makale.objects.filter(anonim_pdf__isnull=False)
    return render(request, 'anonim_makaleler.html', {
        'anonim_makaleler': anonim_makaleler
    })






def hakem_atama(request, takip_no):
    makale = Makale.objects.get(takip_numarasi=takip_no)
    hakemler = Hakem.objects.all()

    if request.method == 'POST':
        secilenler = request.POST.getlist('hakemler')
        for hakem_id in secilenler:
            hakem = Hakem.objects.get(id=hakem_id)
            MakaleHakem.objects.get_or_create(makale=makale, hakem=hakem)

        if secilenler:
            makale.status = "Atandı"
            makale.save()

        log_ekle(makale, "Hakem ataması yapıldı.")
        return HttpResponse("Hakem(ler) başarıyla atandı.")

    return render(request, 'hakem_atama.html', {
        'makale': makale,
        'hakemler': hakemler
    })









def hakem_oner(request, takip_no):
    try:
        makale = Makale.objects.get(takip_numarasi=takip_no)
        pdf_path = makale.pdf.path
        keywords = extract_keywords_from_pdf(pdf_path)
        alanlar = tahmin_et_uzmanlik_alanlari(keywords)
        hakemler = Hakem.objects.filter(uzmanlik_alanlari__in=alanlar).distinct()
    except:
        hakemler = []
        keywords = []
        alanlar = []

    if request.method == 'POST':
        secilenler = request.POST.getlist("hakemler")
        for hakem_id in secilenler:
            hakem = Hakem.objects.get(id=hakem_id)
            MakaleHakem.objects.get_or_create(makale=makale, hakem=hakem)


        if secilenler:
            makale.status = "Atandı"
            makale.save()


        log_ekle(makale, "Hakem ataması yapıldı.")

        return redirect(f"{reverse('anonim_makaleler')}?atama=ok")

    return render(request, 'hakem_oner.html', {
        'makale': makale,
        'keywords': keywords,
        'alanlar': alanlar,
        'hakemler': hakemler
    })





def hakem_paneli(request, slug):
    try:
        hakem = Hakem.objects.get(slug=slug)
        iliskiler = MakaleHakem.objects.filter(hakem=hakem)
        
        for iliski in iliskiler:
            if iliski.durum == "Değerlendirildi" and not iliski.reviewed_pdf:
                pdf_yolu = f"uploads/reviewed/{iliski.makale.takip_numarasi}_{hakem.slug}_reviewed.pdf"
                full_path = os.path.join('media', pdf_yolu)
                
                if os.path.exists(full_path):
                    iliski.reviewed_pdf = pdf_yolu
                    iliski.save()
        
    except Hakem.DoesNotExist:
        return HttpResponse("Hakem bulunamadı.")

    return render(request, 'hakem_paneli.html', {
        'hakem': hakem,
        'iliskiler': iliskiler
    })





from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.core.files import File
import os
import io

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter

from .models import Makale, Hakem, MakaleHakem
from .utils import log_ekle

def makale_degerlendir(request, takip_no, slug):
    try:
        makale = Makale.objects.get(takip_numarasi=takip_no)
        hakem = Hakem.objects.get(slug=slug)
        iliski = MakaleHakem.objects.get(makale=makale, hakem=hakem)
    except:
        return JsonResponse({"success": False, "message": "İlişki bulunamadı."}, status=404)

    if request.method == 'POST':
        yorum = request.POST.get("yorum")
        if not yorum or yorum.strip() == "":
            return JsonResponse({"success": False, "message": "Değerlendirme metni boş olamaz."}, status=400)

        try:
            orijinal_pdf = makale.anonim_pdf.path
            reader = PdfReader(orijinal_pdf)
            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=A4)

            pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
            can.setFont('Arial', 12)


            can.drawString(50, 800, f"Hakem Değerlendirmesi ({hakem.ad}):")

            text_object = can.beginText(50, 770)
            text_object.setFont('Arial', 12)
            for line in yorum.splitlines():
                text_object.textLine(line)
            can.drawText(text_object)
            can.save()

            packet.seek(0)
            yorum_pdf = PdfReader(packet)
            writer.add_page(yorum_pdf.pages[0])

            reviewed_path = f"media/uploads/reviewed/{takip_no}_{hakem.slug}_reviewed.pdf"
            os.makedirs(os.path.dirname(reviewed_path), exist_ok=True)

            with open(reviewed_path, "wb") as out_file:
                writer.write(out_file)

            with open(reviewed_path, "rb") as f:
                iliski.reviewed_pdf.save(f"{takip_no}_{hakem.slug}_reviewed.pdf", File(f), save=False)

            iliski.yorum = yorum
            iliski.durum = "Değerlendirildi"
            iliski.save()

            makale.status = "Değerlendirildi"
            makale.save()

            log_ekle(makale, f"{hakem.ad} adlı hakem değerlendirme yaptı.")

            return JsonResponse({
                "success": True,
                "reviewed_pdf_url": iliski.reviewed_pdf.url,
                "takip_no": str(takip_no)
            })

        except Exception as e:
            return JsonResponse({"success": False, "message": f"PDF oluşturulamadı: {str(e)}"}, status=500)

    return render(request, 'makale_degerlendir.html', {
        'makale': makale,
        'hakem': hakem
    })








from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
import io

def final_pdf_yukle(request, takip_no):
    try:
        makale = Makale.objects.get(takip_numarasi=takip_no)
    except Makale.DoesNotExist:
        return HttpResponse("Makale bulunamadı.")

    orijinal_pdf_path = makale.anonim_pdf.path
    reader = PdfReader(orijinal_pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)

    pdfmetrics.registerFont(TTFont("Arial", "C:/Windows/Fonts/arial.ttf"))  # veya DejaVuSans.ttf

    can.setFont("Arial", 12)
    y_pos = 800

    ek_satirlar = []

    if makale.sifreli_ad:
        ek_satirlar.append("Yazar: " + desifrele(makale.sifreli_ad))
    if makale.sifreli_email:
        ek_satirlar.append("E-Posta: " + desifrele(makale.sifreli_email))
    if makale.sifreli_kurum:
        ek_satirlar.append("Kurum: " + desifrele(makale.sifreli_kurum))

    if ek_satirlar:
        can.drawString(50, y_pos, "De-Anonimleştirme Bilgileri:")
        y_pos -= 25
        for satir in ek_satirlar:
            can.drawString(50, y_pos, satir)
            y_pos -= 20
        y_pos -= 20

    yorumlar = makale.hakem_iliskileri.filter(durum="Değerlendirildi")
    if yorumlar.exists():
        son_yorum = yorumlar.last()
        yorum_metni = son_yorum.yorum or ""
        hakem_adi = son_yorum.hakem.ad

        can.drawString(50, y_pos, f"Hakem Değerlendirmesi ({hakem_adi}):")
        y_pos -= 25

        text_obj = can.beginText(50, y_pos)
        text_obj.setFont("Arial", 12)
        for line in yorum_metni.splitlines():
            text_obj.textLine(line)
        can.drawText(text_obj)

    can.save()
    packet.seek(0)
    ek_pdf = PdfReader(packet)
    writer.add_page(ek_pdf.pages[0])

    final_path = f"media/uploads/final/{takip_no}_final.pdf"
    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    with open(final_path, "wb") as out_file:
        writer.write(out_file)

    with open(final_path, "rb") as f:
        makale.final_pdf.save(f"{takip_no}_final.pdf", File(f), save=True)
        log_ekle(makale, "Final PDF yüklendi ve orijinal bilgiler eklendi.")

    return HttpResponse(f"Final PDF başarıyla oluşturuldu. <a href='/{final_path}'>İndir</a>")






def log_kaydi_goster(request, takip_no):
    try:
        makale = Makale.objects.get(takip_numarasi=takip_no)
        loglar = makale.loglar.order_by('-zaman')
    except Makale.DoesNotExist:
        return HttpResponse("Makale bulunamadı.")

    return render(request, 'log_kaydi.html', {
        'makale': makale,
        'loglar': loglar
    })







def tum_log_kaydi(request):
    loglar = MakaleLog.objects.all().order_by('-zaman')

    loglar_dict = {}
    for log in loglar:
        takip_no = str(log.makale.takip_numarasi)
        if takip_no not in loglar_dict:
            loglar_dict[takip_no] = {'islemler': [], 'tarihler': []}
        loglar_dict[takip_no]['islemler'].append(log.islem)
        loglar_dict[takip_no]['tarihler'].append(log.zaman)

    return render(request, 'tum_log_kaydi.html', {'log_dict': loglar_dict})




def mesaj_paneli(request, takip_no):
    gonderen = request.GET.get("rol", "YAZAR")  

    try:
        makale = Makale.objects.get(takip_numarasi=takip_no)
    except Makale.DoesNotExist:
        return HttpResponse("Makale bulunamadı.")

    mesajlar = makale.mesajlar.order_by('zaman')
    form = MesajForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        mesaj = form.save(commit=False)
        mesaj.makale = makale
        mesaj.gonderen = gonderen
        mesaj.save()

    return render(request, 'mesaj_paneli.html', {
        'makale': makale,
        'mesajlar': mesajlar,
        'form': form,
        'gonderen': gonderen
    })



def editor_mesaj_paneli(request, takip_no):
    gonderen = 'EDITOR'

    makale = get_object_or_404(Makale, takip_numarasi=takip_no)
    mesajlar = makale.mesajlar.order_by("zaman")
    form = MesajForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        mesaj = form.save(commit=False)
        mesaj.makale = makale
        mesaj.gonderen = gonderen
        mesaj.save()

        if request.headers.get('HX-Request'):  # Htmx gibi bir yapı varsa response döndür
            return render(request, 'partials/editor_mesajlar.html', {
                'mesajlar': makale.mesajlar.order_by('zaman'),
            })

    return render(request, 'mesaj_paneli.html', {
        'makale': makale,
        'mesajlar': mesajlar,
        'form': form,
        'gonderen': gonderen
    })



from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
import io

def deanonimlestir(request, takip_no):
    import json, traceback
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from PyPDF2 import PdfReader, PdfWriter

    makale = get_object_or_404(Makale, takip_numarasi=takip_no)

    if not makale.anonim_pdf or not os.path.exists(makale.anonim_pdf.path):
        return HttpResponse("❌ Anonim PDF bulunamadı.")

    try:
        reader = PdfReader(makale.anonim_pdf.path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)

        # Font
        font_path = "C:/Windows/Fonts/arial.ttf"
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("Arial", font_path))
            can.setFont("Arial", 12)
        else:
            can.setFont("Helvetica", 12)

        y = 800
        can.drawString(50, y, "📌 De-Anonimleştirilmiş Bilgiler:")
        y -= 30

        def yaz(json_field, label):
            nonlocal y
            try:
                bilgiler = json.loads(json_field)
                for sifreli in bilgiler:
                    cozulmus = desifrele(sifreli)
                    can.drawString(50, y, f"{label}: {cozulmus}")
                    y -= 20
            except Exception as e:
                can.drawString(50, y, f"{label} çözülemedi: {e}")
                y -= 20

        if makale.sifreli_ad:
            yaz(makale.sifreli_ad, "Yazar")
        if makale.sifreli_email:
            yaz(makale.sifreli_email, "E-posta")
        if makale.sifreli_kurum:
            yaz(makale.sifreli_kurum, "Kurum")

        can.save()
        packet.seek(0)

        ek_sayfa = PdfReader(packet)
        writer.add_page(ek_sayfa.pages[0])

        deanon_path = f"media/uploads/final/{makale.takip_numarasi}_deanon.pdf"
        os.makedirs(os.path.dirname(deanon_path), exist_ok=True)

        with open(deanon_path, "wb") as f:
            writer.write(f)

        with open(deanon_path, "rb") as f:
            makale.final_pdf.save(f"{makale.takip_numarasi}_deanon.pdf", File(f), save=True)
            log_ekle(makale, "Editör tarafından de-anonimleştirme yapıldı.")

        return HttpResponse(f"✅ PDF oluşturuldu. <a href='/{deanon_path}'>İndir</a>")

    except Exception as e:
        return HttpResponse(f"⚠️ Hata: {e}<br><pre>{traceback.format_exc()}</pre>")

