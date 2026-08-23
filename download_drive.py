import os
import io
import zipfile
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def main():
    sa_key_info = os.environ.get('GCP_SA_KEY')
    if not sa_key_info:
        raise ValueError("Secret GCP_SA_KEY tidak ditemukan!")

    target_account = os.environ.get('TARGET_ACCOUNT', '').strip()
    if not target_account:
        print("[!] TARGET_ACCOUNT tidak terdeteksi, unduh dibatalkan.")
        return

    exact_zip_name = f"{target_account}.zip"

    creds_dict = json.loads(sa_key_info)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    print(f"Mencari file SPESIFIK: '{exact_zip_name}' di Drive...")
    
    query = f"name = '{exact_zip_name}' and trashed = false"
    results = service.files().list(
        q=query,
        fields="files(id, name)",
        pageSize=10
    ).execute()

    files = results.get('files', [])

    if not files:
        print(f"[!] PERINGATAN: File '{exact_zip_name}' tidak ditemukan di Drive!")
        return

    for file in files:
        f_id = file['id']
        f_name = file['name']
        print(f"--> Mengunduh {f_name} (ID: {f_id})...")
        
        request = service.files().get_media(fileId=f_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        
        fh.seek(0)
        print(f"--> Mengekstrak {f_name}...")
        try:
            with zipfile.ZipFile(fh, 'r') as zip_ref:
                zip_ref.extractall('.')
            print(f"--> BERHASIL EKSTRAK: {f_name}\n")
        except Exception as e:
            print(f"--> GAGAL EKSTRAK {f_name}: {e}\n")

if __name__ == '__main__':
    main()
