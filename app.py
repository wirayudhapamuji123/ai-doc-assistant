import streamlit as st
from pypdf import PdfReader
import requests

st.set_page_config(page_title="AI Doc-Assistant Pro", layout="wide")
st.title("📄 AI Doc-Assistant Pro ")

api_key = st.sidebar.text_input("Masukkan Google Gemini API Key:", type="password")
uploaded_file = st.file_uploader("Pilih dan unggah file PDF Anda", type=["pdf"])

# 1. Fungsi untuk deteksi otomatis model yang boleh dipakai oleh API Key kamu
def ambil_model_tersedia(key):
    url = f"https://generativelanguage.googleapis.com/v1/models?key={key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            models_data = response.json().get('models', [])
            # Ambil model yang mendukung pembuatan konten text
            daftar_model = [m['name'] for m in models_data if 'generateContent' in m.get('supportedGenerationMethods', [])]
            return daftar_model
        else:
            return []
    except:
        return []

def panggil_gemini_api(model_name, prompt, key):
    # model_name sudah otomatis berisi format lengkap seperti 'models/gemini-1.5-flash' atau varian lainnya
    url = f"https://generativelanguage.googleapis.com/v1/{model_name}:generateContent?key={key}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        if response.status_code == 200:
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error ({response.status_code}): {data.get('error', {}).get('message', 'Gagal request.')}"
    except Exception as e:
        return f"Gagal terhubung: {str(e)}"

# 2. Logika Deteksi Model di Sidebar
model_pilihan = None
if api_key:
    with st.spinner("Mengecek hak akses model Anda ke server Google..."):
        list_model = ambil_model_tersedia(api_key)
    
    if list_model:
        # Bersihkan string nama agar rapi di dropdown (menghilangkan kata 'models/')
        pilihan_user = st.sidebar.selectbox("Pilih Model yang Aktif di Akun Anda:", list_model)
        model_pilihan = pilihan_user
        st.sidebar.success("Koneksi API Key Sukses!")
    else:
        st.sidebar.error("API Key Salah / Tidak Memiliki Akses.")
else:
    st.sidebar.info("Masukkan API Key terlebih dahulu.")

# 3. Proses Dokumen PDF
if uploaded_file and api_key and model_pilihan:
    try:
        reader = PdfReader(uploaded_file)
        teks_dokumen = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    except Exception as e:
        st.error(f"Gagal membaca PDF: {e}")
        teks_dokumen = ""

    if teks_dokumen:
        st.success("Dokumen berhasil dimuat!")
        konteks = teks_dokumen[:8000]
        
        kolom_kiri, kolom_kanan = st.columns(2)
        
        with kolom_kiri:
            st.subheader("📊 Ringkasan Otomatis")
            if st.button("Buat Ringkasan"):
                with st.spinner("AI sedang merangkum..."):
                    hasil = panggil_gemini_api(model_pilihan, f"Ringkas dokumen ini dalam Bahasa Indonesia:\n\n{konteks}", api_key)
                    st.write(hasil)
                    
        with kolom_kanan:
            st.subheader("💬 Tanya Jawab")
            user_question = st.text_input("Tanyakan sesuatu tentang dokumen ini:")
            
            # INI TOMBOL ENTER / KIRIM KHUSUS UNTUK PENGGUNA HP
            if st.button("Kirim"):
                if user_question:
                    with st.spinner("AI sedang mencari jawaban..."):
                        prompt_tanya = f"Berdasarkan dokumen berikut, jawablah pertanyaan user.\n\nDokumen:\n{konteks}\n\nPertanyaan: {user_question}"
                        jawaban = panggil_gemini_api(model_pilihan, prompt_tanya, api_key)
                        st.write(jawaban)
                        jawaban = panggil_gemini_api(model_pilihan, f"Dokumen:\n{konteks}\n\nPertanyaan: {user_question}", api_key)
                        st.write(jawaban)
