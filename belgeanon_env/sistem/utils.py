import fitz  # PyMuPDF
import spacy
import re
from cryptography.fernet import Fernet
import os
import cv2
import numpy as np
from PIL import Image
from collections import Counter
from pdf2image import convert_from_path
import pytesseract
from .models import UzmanlikAlani, MakaleLog
import Levenshtein



nlp = spacy.load("en_core_web_sm")
key = Fernet.generate_key()
cipher = Fernet(key)

def anonymize_text(pdf_path):
    doc = fitz.open(pdf_path)
    all_text = ""

    for page in doc:
        all_text += page.get_text("text")


    ner_results = []
    doc_nlp = nlp(all_text)
    for ent in doc_nlp.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "EMAIL"]:
            ner_results.append(ent.text)

   
    regex_emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", all_text)
    ner_results.extend(regex_emails)

    ner_results = list(set(ner_results))

    encrypted_data = {item: cipher.encrypt(item.encode()).decode() for item in ner_results}
    return encrypted_data




def create_anonymized_pdf(pdf_path, secilecek_veriler, takip_no):
    doc = fitz.open(pdf_path)

    for page in doc:
        text_instances = []

        page_text = page.get_text().lower()

        for hedef in secilecek_veriler:
            metin = hedef.get("text", "").strip()
            if not metin:
                continue

            metin_kucuk = metin.lower()

            if metin_kucuk in page_text:
                rects = page.search_for(metin)  
                text_instances.extend(rects)

        
        for rect in text_instances:
            page.add_redact_annot(rect, fill=(1, 1, 1))

        if text_instances:
            page.apply_redactions()

    anon_folder = os.path.join("media", "uploads", "anon")
    os.makedirs(anon_folder, exist_ok=True)
    anon_path = os.path.join(anon_folder, f"{takip_no}_anon.pdf")
    doc.save(anon_path)
    doc.close()

    return f"/media/uploads/anon/{takip_no}_anon.pdf"







def anonymize_text_by_type(pdf_path, secilen_turler):
    doc = fitz.open(pdf_path)
    all_text = ""
    for page in doc:
        all_text += page.get_text("text")

    
    doc_nlp = nlp(all_text)
    sonuc = []
    
    for ent in doc_nlp.ents:
        if ent.label_ in secilen_turler:
            sonuc.append({
                'label': ent.label_,
                'text': ent.text
            })
    
    if "EMAIL" in secilen_turler:
        regex_emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", all_text)
        for email in set(regex_emails):
            sonuc.append({
                'label': 'EMAIL',
                'text': email
            })
    
    return list({v['text']: v for v in sonuc}.values())  




def anonymize_text_by_type_with_ocr(pdf_path, secilen_turler):
    pages = convert_from_path(pdf_path, 300)
    full_text = ""
    for page in pages:
        text = pytesseract.image_to_string(page, lang='eng')
        full_text += text + "\n"

    sonuc = []
    doc_nlp = nlp(full_text)
    
    for ent in doc_nlp.ents:
        if ent.label_ in secilen_turler:
            sonuc.append({
                'label': ent.label_,
                'text': ent.text
            })

    if "EMAIL" in secilen_turler:
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", full_text)
        for email in set(emails):
            sonuc.append({'label': 'EMAIL', 'text': email})

    return list({v['text']: v for v in sonuc}.values())



def anonymize_text_by_type_with_fallback(pdf_path, secilen_turler):
    try:
        sonuc = anonymize_text_by_type(pdf_path, secilen_turler)

        if not sonuc:
            print("📉 SpaCy sonuç vermedi, OCR fallback devreye giriyor.")
            sonuc = anonymize_text_by_type_with_ocr(pdf_path, secilen_turler)

        return sonuc
    except Exception as e:
        print("❌ Anonimleştirme sırasında hata:", e)
        return []







def blur_sensitive_images(pdf_path, sensitive_words):
    doc = fitz.open(pdf_path)
    for page_index in range(len(doc)):
        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            img_bytes = base_image["image"]
            img_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")

            img_cv = np.array(img_pil)
            img_gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)

            for kelime in sensitive_words:
                if kelime.lower() in base_image["name"].lower():
                    blurred = cv2.GaussianBlur(img_cv, (25, 25), 0)
                    img_cv = blurred

            img_pil_blurred = Image.fromarray(img_cv)
            img_pil_blurred.save(f"media/blurred_page_{page_index}_{img_index}.png")


import re
from pdf2image import convert_from_path
import pytesseract

def extract_keywords_from_text_block(text_block):
    cleaned = re.sub(r'(?i)\b(?:KEYWORDS?|INDEX TERMS?|SUBJECT TERMS?|DESCRIPTORS|TAGS)[^:;—-]*[:;—-]', '', text_block)
    
    cleaned = cleaned.replace("\n", " ").strip()

    if '.' in cleaned:
        cleaned = cleaned.split('.')[0]

    if ";" in cleaned:
        raw_keywords = cleaned.split(";")
    elif "," in cleaned:
        raw_keywords = cleaned.split(",")
    else:
        raw_keywords = [cleaned]

    return [kw.strip().rstrip('.') for kw in raw_keywords if kw.strip()]




def extract_keywords_from_pdf(pdf_path):
    keyword_identifiers = [
        "INDEX TERMS", "KEYWORDS", "KEY WORDS", "KEY TERMS",
        "INDEX", "KEYWORD", "SUBJECT TERMS", "DESCRIPTORS", "TAGS"
    ]

    doc = fitz.open(pdf_path)
    for page in doc:
        lines = page.get_text().split("\n")
        for i, line in enumerate(lines):
            line_upper = line.strip().upper()
            for keyword_id in keyword_identifiers:
                if keyword_id in line_upper:
                    print(f"Anahtar kelime etiketi bulunan satır: '{line.strip()}'")

                    block = line
                    for j in range(i + 1, min(i + 4, len(lines))):
                        next_line = lines[j].strip()
                        if next_line == "":
                            break
                        block += " " + next_line

                    print("Toplanan anahtar kelime bloğu:", block)
                    return extract_keywords_from_text_block(block)

    print("Anahtar kelime bulunamadı.")
    return []






def extract_keywords_from_pdf_with_ocr(pdf_path):
    keyword_identifiers = [
        "INDEX TERMS", "KEYWORDS", "KEY WORDS", "KEY TERMS", 
        "INDEX", "KEYWORD", "SUBJECT TERMS", "DESCRIPTORS", "TAGS"
    ]

    pages = convert_from_path(pdf_path, 300)
    all_text = ""
    for page in pages:
        text = pytesseract.image_to_string(page, lang='eng')
        all_text += text + "\n"

    lines = all_text.split("\n")
    for i, line in enumerate(lines):
        line_upper = line.upper()
        for keyword_id in keyword_identifiers:
            if keyword_id in line_upper:
                print(f"Anahtar kelime etiketi bulunan satır: '{line.strip()}'")

                block = line
                for j in range(i + 1, min(i + 4, len(lines))):
                    next_line = lines[j].strip()
                    if next_line == "":
                        break
                    block += " " + next_line

                print("Toplanan anahtar kelime bloğu:", block)
                return extract_keywords_from_text_block(block)

    print("Anahtar kelime bulunamadı.")
    return []





def tahmin_et_uzmanlik_alanlari(keywords):
    alanlar = UzmanlikAlani.objects.all()
    eslesen_alanlar = []

    for alan in alanlar:
        for keyword in keywords:
            if (
                alan.ana_baslik.lower() in keyword.lower()
                or alan.alt_baslik.lower() in keyword.lower()
                or keyword.lower() in alan.alt_baslik.lower()
            ):
                eslesen_alanlar.append(alan)
                break  
    return list(set(eslesen_alanlar))  




def log_ekle(makale, islem):
    MakaleLog.objects.create(makale=makale, islem=islem)





def generate_key():
    return Fernet.generate_key()


import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

FERNET_KEY = os.getenv("FERNET_KEY")

if not FERNET_KEY:
    raise ValueError("FERNET_KEY .env dosyasından yüklenemedi.")

f = Fernet(FERNET_KEY.encode())

def sifrele(veri: str) -> str:
    return f.encrypt(veri.encode()).decode()

def desifrele(sifreli_veri: str) -> str:
    return f.decrypt(sifreli_veri.encode()).decode()




def tahmin_et_uzmanlik_alanlari(keywords, esik=0.75):
    alanlar = UzmanlikAlani.objects.all()
    eslesen_alanlar = []

    for alan in alanlar:
        for keyword in keywords:
            kw = keyword.lower()
            ana = alan.ana_baslik.lower()
            alt = alan.alt_baslik.lower()

            oran_ana = Levenshtein.ratio(kw, ana)
            oran_alt = Levenshtein.ratio(kw, alt)

            if oran_ana >= esik or oran_alt >= esik:
                eslesen_alanlar.append(alan)
                break  

    return list(set(eslesen_alanlar))  




def anonymize_text_by_type_with_fallback(pdf_path, secilen_turler):
    try:
        sonuc = anonymize_text_by_type(pdf_path, secilen_turler)

        if not sonuc:
            print("📉 SpaCy başarısız, OCR fallback devrede...")
            sonuc = anonymize_text_by_type_with_ocr(pdf_path, secilen_turler)

        return sonuc
    except Exception as e:
        print("❌ Anonimleştirme hatası:", e)
        return []
