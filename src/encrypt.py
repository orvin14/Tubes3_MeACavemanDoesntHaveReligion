import base64
import mysql.connector
from datetime import datetime
ENCRYPTION_KEY = "KunciRahasiaSuperKuatPanjangdanBesar420!"

def xor_encrypt_data(plaintext_str, key_str):
    if plaintext_str is None or not key_str: # Menangani jika plaintext_str adalah None
        return None 
    if not plaintext_str: 
        return "" 

    key_bytes = key_str.encode('utf-8')
    # Pastikan plaintext_str adalah string
    data_bytes = str(plaintext_str).encode('utf-8')
    key_len = len(key_bytes)
    
    encrypted_bytes = bytearray()
    for i in range(len(data_bytes)):
        encrypted_bytes.append(data_bytes[i] ^ key_bytes[i % key_len])
        
    return base64.b64encode(encrypted_bytes).decode('utf-8')

def xor_decrypt_data(ciphertext_base64_str, key_str):
    if not ciphertext_base64_str or not key_str:
        return ciphertext_base64_str
    try:
        encrypted_bytes = base64.b64decode(ciphertext_base64_str.encode('utf-8'))
    except Exception as e:
        print(f"Error saat Base64 decode: {e}")
        return None 

    key_bytes = key_str.encode('utf-8')
    key_len = len(key_bytes)
    
    decrypted_bytes = bytearray()
    for i in range(len(encrypted_bytes)):
        decrypted_bytes.append(encrypted_bytes[i] ^ key_bytes[i % key_len])
        
    try:
        return decrypted_bytes.decode('utf-8')
    except UnicodeDecodeError as e:
        print(f"Error saat UTF-8 decode setelah dekripsi: {e}")
        return None 
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",       
            user="", # Ganti dengan username MySQL           
            password="", # Ganti dengan password MySQL       
            database="" # Ganti dengan nama database    
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error koneksi ke MySQL: {err}")
        return None
    
def get_profile_by_id(applicant_id):
    conn = get_db_connection()
    if conn is None:
        return None
        
    cursor = None
    profil_didekripsi = None
    try:
        cursor = conn.cursor(dictionary=True) 
        query_select = """
            SELECT applicant_id, first_name, last_name, date_of_birth, address, phone_number 
            FROM applicantprofile 
            WHERE applicant_id = %s
        """
        cursor.execute(query_select, (applicant_id,))
        row_encrypted = cursor.fetchone() 
        
        if row_encrypted:
            first_name_dec = xor_decrypt_data(row_encrypted["first_name"], ENCRYPTION_KEY)
            last_name_dec = xor_decrypt_data(row_encrypted["last_name"], ENCRYPTION_KEY)
            date_of_birth_dec = xor_decrypt_data(row_encrypted["date_of_birth"], ENCRYPTION_KEY)
            if date_of_birth_dec:
                try:
                    date_of_birth_obj = datetime.strptime(date_of_birth_dec, '%Y-%m-%d').date()
                    # Sekarang date_of_birth_obj adalah objek datetime.date
                except ValueError:
                    print(f"Format tanggal tidak valid setelah dekripsi: {date_of_birth_dec}")
                    date_of_birth_obj = None 
            address_dec = xor_decrypt_data(row_encrypted["address"], ENCRYPTION_KEY)
            phone_number_dec = xor_decrypt_data(row_encrypted["phone_number"], ENCRYPTION_KEY)
            
            profil_didekripsi = {
                "applicant_id": row_encrypted["applicant_id"], # ID tidak dienkripsi
                "first_name": first_name_dec, 
                "last_name": last_name_dec,
                "date_of_birth": date_of_birth_obj,
                "address": address_dec, 
                "phone_number": phone_number_dec
            }
        else:
            print(f"Profil untuk Applicant ID '{applicant_id}' tidak ditemukan.")
            
    except mysql.connector.Error as err:
        print(f"Error saat mengambil data dari database: {err}")
    except Exception as e:
        print(f"Terjadi error tak terduga saat mengambil profil: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    return profil_didekripsi

def encrypt_database():
    conn = get_db_connection()
    if conn is None:
        print("Tidak bisa terhubung ke database. Proses enkripsi dibatalkan.")
        return

    cursor_select = None
    cursor_update = None
    rows_processed = 0
    rows_failed = 0

    try:
        cursor_select = conn.cursor(dictionary=True)
        query_select_all = "SELECT applicant_id, first_name, last_name, date_of_birth, address, phone_number FROM applicantprofile"
        cursor_select.execute(query_select_all)
        
        all_rows = cursor_select.fetchall()
        if not all_rows:
            print("Tidak ada data di tabel applicantprofile untuk dienkripsi.")
            return

        print(f"Ditemukan {len(all_rows)} baris untuk diproses...")
        cursor_update = conn.cursor()

        for row in all_rows:
            applicant_id = row["applicant_id"]

            try:
                print(f"Memproses applicant_id: {applicant_id}...")
                first_name_enc = xor_encrypt_data(row["first_name"], ENCRYPTION_KEY)
                last_name_enc = xor_encrypt_data(row["last_name"], ENCRYPTION_KEY)
                date_of_birth_enc = xor_encrypt_data(str(row["date_of_birth"]), ENCRYPTION_KEY)
                address_enc = xor_encrypt_data(row["address"], ENCRYPTION_KEY)
                phone_number_enc = xor_encrypt_data(row["phone_number"], ENCRYPTION_KEY)

                query_update = """
                    UPDATE applicantprofile 
                    SET first_name = %s, last_name = %s, date_of_birth = %s, address = %s, phone_number = %s
                    WHERE applicant_id = %s
                """
                cursor_update.execute(query_update, (
                    first_name_enc, last_name_enc, date_of_birth_enc, address_enc, phone_number_enc,
                    applicant_id
                ))
                rows_processed += 1
            except Exception as e_row:
                print(f"Error saat mengenkripsi atau mengupdate applicant_id {applicant_id}: {e_row}")
                rows_failed += 1
                conn.rollback() 
        if rows_failed == 0 and rows_processed > 0:
            conn.commit()
            print(f"Enkripsi selesai. {rows_processed} baris berhasil diproses.")
        elif rows_processed > 0: # Ada beberapa yang berhasil, beberapa gagal
            conn.commit()
            print(f"Enkripsi selesai dengan beberapa kegagalan. {rows_processed} baris berhasil diproses, {rows_failed} baris gagal.")
        elif rows_failed > 0 :
            print(f"Enkripsi gagal untuk semua baris yang dicoba ({rows_failed} baris). Tidak ada perubahan di-commit.")
            conn.rollback() # Pastikan rollback jika semua gagal
        else:
            print("Tidak ada baris yang diproses atau memerlukan update.")


    except mysql.connector.Error as err_db:
        print(f"Error database selama proses enkripsi batch: {err_db}")
        if conn:
            conn.rollback()
    except Exception as e_main:
        print(f"Error tak terduga selama proses enkripsi batch: {e_main}")
        if conn:
            conn.rollback()
    finally:
        if cursor_select:
            cursor_select.close()
        if cursor_update:
            cursor_update.close()
        if conn and conn.is_connected():
            conn.close()