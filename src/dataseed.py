import os
import mysql.connector
from mysql.connector import errorcode
from pathlib import Path

# --- KONFIGURASI ---
script_dir = Path(__file__).resolve().parent
project_dir = script_dir.parent
FOLDER_PATH = str(project_dir / 'datum')

PREFIKS_UNTUK_CV_PATH = "../data/"

MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'admin'
MYSQL_DATABASE = 'datastima'

TABLE_NAME = 'ApplicationDetail'
MAKS_FILE_PER_SUBFOLDER = 20
# --- AKHIR KONFIGURASI ---

def dapatkan_info_file_dari_folder_nested(base_folder_path, prefiks_cv_path, maks_file_per_subfolder):
    """
    Mendapatkan informasi file dari folder bersarang.
    Mengambil hingga 'maks_file_per_subfolder' dari setiap subfolder.
    'applicant_id' akan 1, 2, ..., N untuk setiap subfolder.
    """
    semua_file_info_final = []
    try:
        base_folder_path_str = str(base_folder_path)
        if not os.path.isdir(base_folder_path_str):
            print(f"⚠️ Error: Folder utama '{base_folder_path_str}' bukan direktori atau tidak ditemukan.")
            return []

        nama_subfolder_list = sorted([
            item for item in os.listdir(base_folder_path_str)
            if os.path.isdir(os.path.join(base_folder_path_str, item))
        ])

        for nama_subfolder in nama_subfolder_list:
            path_subfolder = os.path.join(base_folder_path_str, nama_subfolder)
            
            files_di_subfolder_mentah = []
            for nama_file in os.listdir(path_subfolder):
                if os.path.isfile(os.path.join(path_subfolder, nama_file)):
                    files_di_subfolder_mentah.append(nama_file)
            
            files_di_subfolder_mentah.sort() # Urutkan file dalam subfolder
            
            file_terpilih_dari_subfolder = files_di_subfolder_mentah[:maks_file_per_subfolder]
            
            # Assign applicant_id mulai dari 1 untuk subfolder ini
            for idx_subfolder, nama_file_terpilih in enumerate(file_terpilih_dari_subfolder):
                applicant_id_subfolder = idx_subfolder + 1 # Reset untuk setiap subfolder
                cv_path_untuk_db = f"{prefiks_cv_path}{nama_file_terpilih}"
                semua_file_info_final.append({
                    "cv_path": cv_path_untuk_db,
                    "application_role": nama_subfolder,
                    "applicant_id": applicant_id_subfolder # applicant_id spesifik subfolder
                })
        
        return semua_file_info_final

    except Exception as e:
        print(f"💥 Error saat membaca folder bersarang: {e}")
        return []

def setup_database_dan_tabel_mysql(host, user, password, db_name, table_name):
    """
    Membuat koneksi ke database MySQL dan membuat tabel ApplicationDetail jika belum ada.
    """
    try:
        conn = mysql.connector.connect(
            host=host, user=user, password=password, database=db_name
        )
        cursor = conn.cursor()
        # detail_id adalah AUTO_INCREMENT PRIMARY KEY, akan diurus oleh MySQL untuk keunikan global
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            detail_id INT AUTO_INCREMENT PRIMARY KEY,
            applicant_id INT NOT NULL, 
            application_role VARCHAR(100) DEFAULT NULL,
            cv_path TEXT DEFAULT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        ''')
        conn.commit()
        print(f"Tabel '{table_name}' siap digunakan di database '{db_name}'.")
        return conn, cursor
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Error: Ada masalah dengan username atau password MySQL Anda.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print(f"Error: Database '{db_name}' tidak ditemukan. Mohon buat terlebih dahulu.")
        else:
            print(f"Error koneksi MySQL: {err}")
        return None, None

def masukkan_info_file_ke_db_mysql(conn, cursor, table_name, daftar_info_file_terpilih):
    """
    Memasukkan informasi file ke dalam tabel ApplicationDetail.
    Menggunakan applicant_id yang sudah ada di file_info.
    """
    jumlah_dimasukkan = 0
    query = f"INSERT INTO {table_name} (applicant_id, application_role, cv_path) VALUES (%s, %s, %s)"

    for file_info in daftar_info_file_terpilih:
        applicant_id = file_info["applicant_id"] # Ambil applicant_id yang sudah di-assign per subfolder
        application_role = file_info["application_role"]
        cv_path = file_info["cv_path"]
        
        try:
            cursor.execute(query, (applicant_id, application_role, cv_path))
            jumlah_dimasukkan += 1
        except mysql.connector.errors.IntegrityError as err:
            print(f"Info: Gagal memasukkan data untuk cv_path '{cv_path}' (applicant_id: {applicant_id} untuk role: {application_role}). Kemungkinan masalah constraint: {err}")
        except mysql.connector.Error as err:
            print(f"Error MySQL saat memasukkan data untuk cv_path '{cv_path}': {err}")
    
    if jumlah_dimasukkan > 0:
        conn.commit()
    return jumlah_dimasukkan

def main():
    print(f"Membaca file dari folder utama: {FOLDER_PATH}")
    print(f" mengambil hingga {MAKS_FILE_PER_SUBFOLDER} file dari setiap subfolder.")

    daftar_file_info_terpilih = dapatkan_info_file_dari_folder_nested(
        FOLDER_PATH, PREFIKS_UNTUK_CV_PATH, MAKS_FILE_PER_SUBFOLDER
    )

    if not daftar_file_info_terpilih:
        print("Tidak ada file yang akan diproses.")
        return

    print(f"Total ditemukan {len(daftar_file_info_terpilih)} file untuk dimasukkan:")
    # Mencetak beberapa contoh file pertama jika daftarnya panjang
    for i, info in enumerate(daftar_file_info_terpilih[:10]):
        print(f"  Urutan ke-{i+1} (Detail ID akan otomatis): AppID: {info['applicant_id']}, Role: {info['application_role']}, Path: {info['cv_path']}")
    if len(daftar_file_info_terpilih) > 10:
        print(f"  ... dan {len(daftar_file_info_terpilih) - 10} file lainnya.")

    conn = None
    try:
        conn, cursor = setup_database_dan_tabel_mysql(
            MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, TABLE_NAME
        )

        if conn and cursor:
            print(f"\n⚙️ Memasukkan informasi file ke database MySQL '{MYSQL_DATABASE}', tabel '{TABLE_NAME}'...")
            jumlah_berhasil = masukkan_info_file_ke_db_mysql(conn, cursor, TABLE_NAME, daftar_file_info_terpilih)
            print(f"Selesai. Berhasil memasukkan {jumlah_berhasil} baris data baru.")

    except Exception as e:
        print(f"Terjadi kesalahan tak terduga: {e}")
    finally:
        if conn and conn.is_connected():
            if 'cursor' in locals() and cursor:
                 cursor.close()
            conn.close()
            print("Koneksi database MySQL ditutup.")

if __name__ == '__main__':
    main()