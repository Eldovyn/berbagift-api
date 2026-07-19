# 1. Response API
## 1.1 Response Status Code :
### 1.1.1 untuk method post:
- jika berhasil kembalikan status code 201 (wajib)
- jika validasi gagal kembalikan status code 400 (wajib)
- jika database conflict kembalikan status code 409 (wajib)
- jika data tidak ditemukan kembalikan status code 404 (wajib)

### 1.1.2 untuk method put:
- jika berhasil kembalikan status code 201 (wajib)
- jika validasi gagal kembalikan status code 400 (wajib)
- jika database conflict kembalikan status code 409 (wajib)
- jika data tidak ditemukan kembalikan status code 404 (wajib)
- untuk method put digunakan untuk update sebagian data

### 1.1.3 untuk method patch:
- jika berhasil kembalikan status code 201 (wajib)
- jika validasi gagal kembalikan status code 400 (wajib)
- jika database conflict kembalikan status code 409 (wajib)
- jika data tidak ditemukan kembalikan status code 404 (wajib)
- untuk method patch digunakan untuk update seluruh data

### 1.1.4 untuk method get:
- jika berhasil kembalikan status code 200 (wajib)
- jika validasi gagal kembalikan status code 400 (wajib)
- jika database conflict kembalikan status code 409 (wajib)
- jika data tidak ditemukan kembalikan status code 404 (wajib)
- untuk method get digunakan untuk mengambil data

### 1.1.5 penjelasan atribut2 api:
- message: pesan informasi (wajib)
- data: data yang dikirimkan jika tidak ada data maka kembalikan None (wajib)
- errors: data error yang dikirimkan wajib berupa dictionary atau None (wajib)

## 1.2 Format Response API:
### 1.2.1 untuk status code 201:
- status code digunakan untuk method post, put, patch, dan delete

```json
{
  "message": "string",
  "data": "json",
  "errors": null
}
```

contoh :
```json
{
	"message": "Permintaan berhasil diproses",
	"data": {
    "username": "adit"
  },
	"errors": null
}
```

### 1.2.2 untuk status code 400:
- status code digunakan untuk method post, put, patch, dan delete
- di gunakan jika ada validasi error

```json
{
  "message": "string",
  "data": null,
  "errors": "json"
}
```

contoh :
```json
{
	"message": "gagal memproses permintaan",
	"data": null,
	"errors": {
    "key": "IS_REQUIRED"
  }
}
```

### 1.2.3 untuk status code 409:
- status code digunakan untuk method post, put, patch, dan delete
- di gunakan jika ada database conflict

```json
{
  "message": "string",
  "data": null,
  "errors": null
}
```

### 1.2.4 untuk status code 404:
- status code digunakan untuk method post, put, patch, get, dan delete
- di gunakan jika data tidak ditemukan

```json
{
  "message": "string",
  "data": null,
  "errors": null
}
```

### 1.2.5 untuk status code 500:
- status code digunakan untuk method post, put, patch, get, dan delete
- di gunakan jika ada error

```json
{
  "message": "string",
  "data": null,
  "errors": null
}
```

## 1.3 Error Code List:
- di gunakan untuk field errors pada response api
- untuk error codenya: IS_REQUIRED, IS_INVALID, TOO_LONG, TOO_SHORT, MUST_LOWER, MUST_UPPER, MUST_SYMBOL, MUST_NUMBER, IS_ALREADY

## 1.4 Standarisasi Validation:
- untuk username, nama team, nama lengkap, dll (kecuali link) maksimal 50 karakter
- untuk seluruh data email maksimal 100 karakter
- untuk dateline jangan gunakan tipe data string

# 2. Struktur Folder
- main.py untuk file utama
- keys/ folder untuk menyimpan keys seperti private.pem, public.pem, dll
- routes/ folder untuk menyimpan route
- schemas/ folder untuk menyimpan schema
- templates/ folder untuk menyimpan template
- utils/ folder untuk menyimpan utils
- requirements.txt untuk dependencies
- controllers/ folder untuk menyimpan controller
- databases/ folder untuk menyimpan crud database
- models/ folder untuk menyimpan model
- configs/ folder untuk menyimpan config

## 2.1 Penjelasan Folder:
### 2.1.1 controllers/ :
- untuk setiap file pada controllers silahkan bungkus pakai class

### 2.1.2 databases/ :
- untuk setiap file pada databases silahkan bungkus pakai class

