# CV Keyword Scanner

![image](https://github.com/user-attachments/assets/8f4e6970-12d2-439a-b365-fb9fd4a06935)

Aplikasi desktop sederhana yang dibuat dengan Python dan Tkinter untuk memindai dan menganalisis file CV (dalam format PDF) berdasarkan kata kunci (keyword) yang diberikan. Aplikasi ini membantu recruiter atau HR dalam menyaring kandidat secara efisien dengan menemukan kecocokan keyword di dalam database CV pelamar. Fitur utama aplikasi ini adalah kemampuannya untuk menggunakan algoritma pencarian string yang berbeda (KMP, Boyer-Moore, dan Aho-Corasick) serta melakukan pencarian fuzzy (menggunakan Levenshtein distance) jika pencocokan eksak tidak ditemukan.

##Penjelasan Singkat Algoritma
Aplikasi ini mengimplementasikan dua algoritma pencarian string klasik untuk menemukan pencocokan kata kunci yang eksak:

**1. Knuth-Morris-Pratt (KMP)**
Algoritma KMP bekerja dengan cara yang cerdas untuk menghindari pergeseran karakter satu per satu saat terjadi ketidakcocokan. Sebelum pencarian dimulai, KMP melakukan pra-pemrosesan pada pattern (kata kunci) untuk membangun sebuah tabel (disebut Longest Proper Prefix which is also Suffix atau LPS array). Tabel ini menyimpan informasi tentang awalan terpanjang dari pattern yang juga merupakan akhiran. Ketika ketidakcocokan terjadi, algoritma menggunakan tabel ini untuk "melompat" maju ke posisi berikutnya yang paling mungkin cocok, sehingga mengurangi jumlah perbandingan yang tidak perlu dan meningkatkan efisiensi.

**2. Boyer-Moore (BM)**
Algoritma Boyer-Moore adalah salah satu algoritma pencarian string paling efisien dalam praktik. Pendekatannya unik karena memulai perbandingan dari karakter terakhir pattern, bukan dari awal. Ketika terjadi ketidakcocokan, BM menggunakan dua aturan (heuristik) untuk melakukan pergeseran besar:
Bad Character Heuristic: Jika karakter di dalam teks yang tidak cocok dengan pattern ada di tempat lain di dalam pattern, maka pattern digeser agar karakter tersebut sejajar.
Good Suffix Heuristic: Jika sebagian akhir dari pattern sudah cocok (disebut good suffix), pattern akan digeser untuk menyejajarkan kemunculan good suffix tersebut selanjutnya.
Kombinasi kedua aturan ini membuat BM sangat cepat, terutama pada teks yang panjang dan alfabet yang besar.

**3. Levenshtein**
Berbeda dengan algoritma eksak, pencarian fuzzy bertujuan menemukan kata yang "mirip", meskipun tidak sama persis. Aplikasi ini menggunakan Levenshtein Distance untuk mengukur perbedaan antara dua string.
Jarak Levenshtein menghitung jumlah minimum operasi (sisip, hapus, atau ganti karakter) yang diperlukan untuk mengubah satu kata menjadi kata lainnya. Jika jarak antara sebuah kata di dalam CV dengan kata kunci yang dicari berada di bawah ambang batas tertentu, kata tersebut dianggap sebagai kecocokan fuzzy. Ini sangat berguna untuk mengatasi kesalahan pengetikan (typo) atau variasi kata.


**4. Aho-Corasick**
Algoritma Aho-Corasick adalah ekstensi dari KMP yang dirancang untuk mencari semua kemunculan dari beberapa kata kunci sekaligus dalam satu kali proses. Algoritma ini membangun sebuah struktur data seperti finite state machine (atau automaton) dari semua kata kunci yang diberikan.
Saat teks diproses, Aho-Corasick bergerak melalui status-status di automaton tersebut. Keunggulannya adalah efisiensi yang luar biasa saat mencari banyak kata kunci, karena teks hanya perlu dibaca sekali, tidak peduli berapa banyak kata kunci yang dicari.

## Requirements & Instalasi

Pastikan Anda memiliki lingkungan dan pustaka yang dibutuhkan sebelum menjalankan aplikasi.
Prasyarat:
Python 3.8 atau versi yang lebih baru.
Server MySQL atau MariaDB yang sedang berjalan.
pip package manager untuk Python.

## Instalasi Pustaka Python:

Buka terminal atau command prompt, lalu instal pustaka yang diperlukan menggunakan perintah berikut:
pip install mysql-connector-python PyMuPDF
mysql-connector-python: Untuk menghubungkan aplikasi dengan database MySQL.
PyMuPDF: Untuk mengekstrak teks dari dokumen PDF.
Tkinter: Biasanya sudah termasuk dalam instalasi standar Python. Jika tidak, Anda mungkin perlu menginstalnya secara manual sesuai dengan sistem operasi Anda (misalnya, sudo apt-get install python3-tk di Ubuntu).

## Cara Menjalankan Program
Ikuti langkah-langkah berikut untuk menjalankan aplikasi:
Clone atau Unduh Proyek
Jika proyek ini ada di repositori Git, clone dengan perintah:
```
git clone https://github.com/orvin14/Tubes3_MeACavemanDoesntHaveReligion.git
cd path/to/project/
cd src
```
Atau cukup unduh dan ekstrak file proyek ke dalam satu folder.

## Setup Database
Pastikan server MySQL Anda berjalan.
Create database datastima.
Impor skema tabel yang dibutuhkan (applicantprofile, applicationdetail, dll.). Pastikan untuk membuat tabel sesuai dengan struktur yang diharapkan oleh program.
```
mysql -u <username> -p datastima < dataenc.sql>
```
Jalankan datastima dengan "use datastima".
Ubah detail koneksi database (host, user, password, nama database) di dalam file encrypt.py.

## Jalankan Aplikasi
Buka terminal atau command prompt di direktori proyek, lalu eksekusi script utama:
python gui.py

## Author
Me A Caveman Doesnt Have Religion
| Nama | NIM |
| Orvin Andika Ikhsan Abhista | 13523017 |
| Ferdinand Gabetua Sinaga | 13523051 |
| Salman Hanif | 13523056 |
