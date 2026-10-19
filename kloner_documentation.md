# Dokumentasi `kloner.py`

## 1. Ringkasan

`kloner.py` adalah tool berbasis Python untuk menyalin direktori website ke folder ekspor baru, memeriksa form HTML, dan mengubah tujuan (`action`) form serta endpoint API JavaScript tertentu agar mengarah ke URL server baru.

Fitur utamanya:
- Menyalin folder sumber ke folder ekspor.
- Mengaudit form HTML beserta metode dan field input-nya.
- Mengubah atribut `action` pada elemen `<form>`.
- Mengubah `formaction` pada tombol atau input yang memilikinya.
- Secara opsional, mengubah pemanggilan endpoint JavaScript yang dikenali.
- Membuat laporan audit dalam format JSON.
- Menyediakan mode `--dry-run` untuk melihat rencana pemrosesan tanpa menyalin atau menulis file.

> **Catatan penggunaan yang bertanggung jawab:** gunakan tool ini hanya pada website atau salinan website yang Anda miliki atau telah mendapat izin untuk diuji. Periksa semua endpoint hasil rewrite sebelum menjalankan situs hasil ekspor. Jangan arahkan form untuk mengumpulkan kredensial atau data pribadi tanpa persetujuan dan dasar yang sah.

## 2. Persyaratan

- Python 3.8 atau lebih baru disarankan.
- Dependensi Python: `beautifulsoup4`.

Pasang dependensi:

```bash
python -m pip install beautifulsoup4
```

Simpan script sebagai `kloner.py` atau gunakan nama file yang tersedia di proyek Anda.

## 3. Cara menjalankan

Bentuk umum:

```bash
python kloner.py <direktori_sumber> --new-url <URL_TUJUAN> [opsi]
```

Contoh:

```bash
python kloner.py ./website-copy \
  --new-url https://staging.example.test/submit \
  --output-dir ./exported-site
```

Perintah tersebut menyalin `./website-copy` ke `./exported-site`, lalu memproses file HTML/HTM di folder ekspor dan menyimpan laporan audit JSON.

Jika `--output-dir` tidak ditentukan, nama folder keluaran default adalah `newServer`.

## 4. Argumen CLI

| Argumen | Wajib | Default | Fungsi |
|---|---:|---|---|
| `target` | Ya | — | Path file atau direktori sumber. |
| `-u`, `--new-url` | Ya | — | URL dasar tujuan rewrite. |
| `-out`, `--output-dir` | Tidak | `newServer` | Folder keluaran ekspor. |
| `-b`, `--base-url` | Tidak | kosong | URL dasar asli untuk menyelesaikan path relatif saat audit. |
| `-k`, `--keep-path` | Tidak | `false` | Pertahankan path URL lama ketika membentuk URL baru. |
| `--js` | Tidak | `false` | Aktifkan pemrosesan pola endpoint JavaScript tertentu dan penambahan file `.js` ke daftar pemrosesan. |
| `--dry-run` | Tidak | `false` | Tampilkan hasil audit/rencana rewrite tanpa menyalin atau menulis file. |

### Contoh penggunaan opsi

**Menentukan folder output:**

```bash
python kloner.py ./website-copy -u https://staging.example.test/submit -out ./build
```

**Mempertahankan path endpoint:**

```bash
python kloner.py ./website-copy \
  -u https://staging.example.test/ \
  --keep-path
```

**Mengaktifkan rewrite JavaScript:**

```bash
python kloner.py ./website-copy \
  -u https://staging.example.test/submit \
  --js
```

**Pratinjau tanpa perubahan file:**

```bash
python kloner.py ./website-copy \
  -u https://staging.example.test/submit \
  --js \
  --dry-run
```

## 5. Cara kerja

1. Script membaca argumen command line.
2. Memeriksa apakah path sumber tersedia.
3. Jika bukan `--dry-run`, folder output yang sudah ada akan **dihapus seluruhnya** lalu dibuat ulang dari sumber. Jika sumber berupa file, file tersebut disalin ke folder output.
4. Mengumpulkan file HTML dan HTM secara rekursif. Jika `--js` aktif, file `.js` juga dimasukkan.
5. Untuk setiap file yang diproses, script:
   - Membaca teks UTF-8 (karakter yang gagal didekode diabaikan).
   - Mem-parsing konten menggunakan BeautifulSoup.
   - Mencatat form, metode, dan jumlah field.
   - Mengubah tujuan form dan `formaction` yang ditemukan.
   - Jika `--js` aktif, mencoba mengubah endpoint JavaScript yang cocok dengan pola regex.
6. Menulis file yang berubah ke lokasi kerja.
7. Menulis `pipeline_audit_report.json` ke folder output saat bukan mode dry-run.

## 6. Aturan rewrite URL

Tool membentuk URL baru melalui fungsi `build_new_endpoint()`.

### Tanpa `--keep-path`

Path lama tidak dipertahankan. Tujuan baru menjadi nilai `--new-url`.

Contoh:

| Tujuan lama | `--new-url` | Hasil |
|---|---|---|
| `/api/login` | `https://staging.example.test/submit` | `https://staging.example.test/submit` |
| `https://old.example.test/send` | `https://staging.example.test/submit` | `https://staging.example.test/submit` |

### Dengan `--keep-path`

Path dari URL lama dipertahankan dan digabungkan dengan URL baru. Query string lama juga disertakan.

Contoh:

| Tujuan lama | `--new-url` | Hasil yang diharapkan |
|---|---|---|
| `/api/login` | `https://staging.example.test/` | `https://staging.example.test/api/login` |
| `https://old.example.test/api/login?mode=test` | `https://staging.example.test/` | `https://staging.example.test/api/login?mode=test` |

Perhatikan bahwa path yang dipertahankan berasal dari URL lama; URL fragment (`#...`) tidak dipertahankan oleh fungsi tersebut.

### `--base-url`

`--base-url` digunakan untuk menampilkan tujuan asli yang sudah di-resolve pada laporan audit, terutama jika `action` berisi path relatif. Opsi ini tidak menentukan tujuan rewrite; tujuan rewrite ditentukan oleh `--new-url` dan `--keep-path`.

## 7. HTML yang diproses

Untuk setiap elemen `<form>`, script mencatat:
- Nomor urut form.
- `id` form.
- Metode form (`GET` jika atribut `method` tidak ada).
- Tujuan asli, dengan resolusi relatif opsional melalui `--base-url`.
- Jumlah field yang ditemukan.

Field yang dihitung meliputi:
- `<input>`
- `<textarea>`
- `<select>`
- `<button>`

Metadata setiap field yang dikumpulkan oleh fungsi audit mencakup tag, tipe, `name`, `id`, dan `placeholder`. Laporan JSON saat ini menyimpan jumlah field, bukan daftar metadata field tersebut.

Script juga mengubah:
- Atribut `action` pada setiap `<form>`.
- Atribut `formaction` pada `<button>` atau `<input>` di dalam form jika atribut itu tersedia.

**Batasan:** elemen `formaction` di luar elemen `<form>` tidak diproses oleh loop saat ini. Form tanpa atribut `action` juga akan diberi tujuan baru berdasarkan aturan rewrite.

## 8. Endpoint JavaScript

Opsi `--js` mengaktifkan pola rewrite untuk endpoint literal yang cocok dengan pola berikut:

- `fetch("...")`
- `axios.get(...)`, `axios.post(...)`, `axios.put(...)`, `axios.delete(...)`, `axios.patch(...)`
- `$.get(...)`, `$.post(...)`, dan bentuk tertentu dari `$.ajax(...)`

Contoh bentuk yang dapat dikenali:

```javascript
fetch("/api/status");
axios.post("/api/data", payload);
$.get("/api/items");
```

Pencocokan memakai regex, bukan parser JavaScript. Karena itu, pola yang memakai variabel, template string kompleks, format kode berbeda, atau konstruksi dinamis mungkin tidak terdeteksi atau tidak diubah dengan benar.

**Penting:** walaupun file `.js` ditambahkan ke daftar saat `--js` aktif, implementasi saat ini hanya menjalankan pemrosesan regex JavaScript pada elemen `<script>` yang ditemukan di dokumen yang diparse sebagai HTML. File `.js` eksternal yang diproses langsung tidak diparse sebagai elemen `<script>`, sehingga endpoint di dalam file JavaScript eksternal tidak otomatis di-rewrite oleh logika saat ini.

## 9. Laporan audit JSON

Jika bukan mode `--dry-run`, laporan ditulis ke:

```text
<output-dir>/pipeline_audit_report.json
```

Struktur setiap entri laporan berisi:
- `file`: path file yang diproses.
- `forms`: daftar form yang ditemukan, dengan indeks, ID, metode, tujuan asli, dan jumlah field.
- `rewrites_performed`: daftar perubahan yang dilakukan atau direncanakan pada atribut form dan endpoint JavaScript.

Contoh struktur ringkas:

```json
[
  {
    "file": "exported-site/index.html",
    "forms": [
      {
        "form_index": 1,
        "id": "contact-form",
        "method": "POST",
        "original_destination": "https://original.example.test/contact",
        "fields_count": 3
      }
    ],
    "rewrites_performed": [
      "Form #1 action: '/contact' -> 'https://staging.example.test/submit'"
    ]
  }
]
```

Contoh di atas hanya ilustrasi format, bukan hasil eksekusi pada website tertentu.

## 10. Mode `--dry-run`

Mode ini:
- Tidak menyalin folder/file sumber ke output.
- Tidak menulis perubahan ke file.
- Tetap membaca dan menganalisis file pada path sumber.
- Menampilkan ringkasan proses di terminal.

Catatan implementasi: script masih membentuk daftar kandidat file dan menjalankan fungsi pemrosesan. Perubahan dilakukan pada objek parse di memori, tetapi tidak ditulis ke disk.

## 11. Batasan dan hal yang perlu diperhatikan

- Jika folder output sudah ada, script menghapus folder itu sebelum ekspor. Pastikan path output benar dan tidak menunjuk ke data penting.
- Pemrosesan file HTML dibatasi pada ekstensi `.html` dan `.htm`.
- Pemrosesan JavaScript memakai regex sederhana dan tidak memahami keseluruhan sintaks JavaScript.
- `--base-url` hanya memengaruhi tujuan asli yang ditampilkan pada audit.
- `processed_count` menghitung file yang memiliki form, bukan seluruh file yang dipindai.
- Dalam mode `--dry-run`, label output tetap ditampilkan, tetapi file tidak diekspor.
- Laporan hanya memasukkan file ke `all_audits` jika file tersebut memiliki setidaknya satu form. Karena itu, rewrite JavaScript pada file tanpa form mungkin tidak tercantum di laporan JSON.
- Jika sumber berupa satu file dan bukan direktori, file itu disalin ke folder output. Pastikan file yang diberikan memang HTML jika ingin perilaku parsing HTML.
- Script tidak menjalankan server tujuan, tidak menguji apakah endpoint tujuan tersedia, dan tidak memvalidasi bahwa aplikasi hasil ekspor berfungsi.

## 12. Alur kerja yang disarankan

1. Buat salinan sumber yang dapat dipulihkan.
2. Jalankan `--dry-run` terlebih dahulu.
3. Periksa tujuan URL lama dan rencana rewrite di terminal.
4. Gunakan folder output khusus yang tidak berisi data penting.
5. Jalankan ekspor tanpa `--dry-run`.
6. Tinjau `pipeline_audit_report.json` dan diff file hasil ekspor.
7. Uji form dan endpoint di lingkungan staging yang diotorisasi.

## 13. Troubleshooting

**`Source path ... does not exist`**
- Periksa path sumber dan direktori kerja terminal.
- Gunakan path absolut jika path relatif membingungkan.

**Tidak ada file yang diproses**
- Pastikan direktori berisi file `.html` atau `.htm`.
- File `.js` hanya ditambahkan ke daftar saat `--js` aktif, tetapi perlu diingat batasan pemrosesan JavaScript eksternal di atas.

**Endpoint tidak berubah**
- Pastikan `--new-url` diberikan.
- Pastikan `--js` aktif jika endpoint berada pada JavaScript inline.
- Periksa apakah endpoint ditulis sebagai literal yang cocok dengan regex.
- Pastikan file tersebut berada dalam daftar file yang diproses.

**Hasil ekspor menghapus data output sebelumnya**
- Ini perilaku yang disengaja pada implementasi sekarang: folder output yang sudah ada dihapus sebelum ekspor. Pulihkan dari backup jika diperlukan.

## 14. Ringkasan

`kloner.py` adalah pipeline ekspor salinan website dengan audit form dan rewrite tujuan. Opsi pentingnya adalah `--new-url`, `--output-dir`, `--keep-path`, `--js`, dan `--dry-run`. Karena tool melakukan modifikasi URL dan dapat menghapus folder output lama, jalankan pratinjau terlebih dahulu dan gunakan hanya pada aset serta lingkungan yang Anda berwenang kelola.
