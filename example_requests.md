# Example Request Bodies for Multipart Form Data

## Board Members - POST /board-members/

**Form Data:**
- `data`: JSON string
- `image`: File upload (required)

**JSON Data Example:**
```json
{
  "name": "Dr. Siti Nurhaliza",
  "position": "Kepala Sekolah",
  "description": "Kepala Sekolah dengan pengalaman 15 tahun dalam bidang pendidikan. Memiliki visi untuk mengembangkan sekolah menjadi institusi pendidikan terdepan.",
  "is_active": true,
  "display_order": 1
}
```

---

## Articles - POST /articles/

**Form Data:**
- `data`: JSON string  
- `image`: File upload (required)

**JSON Data Example:**
```json
{
  "title": "Prestasi Siswa dalam Olimpiade Matematika Nasional",
  "description": "Siswa-siswa SMA Negeri 1 Jakarta kembali menorehkan prestasi membanggakan dalam Olimpiade Matematika Nasional tahun 2024. Tim yang terdiri dari 5 siswa berhasil meraih 2 medali emas dan 3 medali perak.\n\nPrestasi ini tidak lepas dari bimbingan intensif dari guru-guru matematika yang berpengalaman serta dukungan penuh dari pihak sekolah. Program persiapan dimulai sejak 6 bulan sebelum kompetisi dengan latihan rutin setiap hari.\n\nKepala Sekolah menyampaikan apresiasi tinggi atas pencapaian ini dan berharap dapat memotivasi siswa lain untuk terus berprestasi dalam bidang akademik.",
  "slug": "prestasi-siswa-olimpiade-matematika-2024",
  "excerpt": "Siswa SMA Negeri 1 Jakarta meraih 2 emas dan 3 perak dalam Olimpiade Matematika Nasional 2024",
  "category": "prestasi",
  "is_published": true,
  "published_at": "2024-01-15T10:00:00"
}
```

---

## Galleries - POST /galleries/

**Form Data:**
- `data`: JSON string
- `image`: File upload (required)

**JSON Data Example:**
```json
{
  "title": "Upacara Bendera Hari Senin",
  "excerpt": "Suasana khidmat upacara bendera yang diselenggarakan setiap hari Senin di halaman sekolah dengan partisipasi seluruh siswa dan guru",
  "is_active": true,
  "display_order": 3
}
```

## Important Notes:

1. **DateTime Format**: Use ISO format without timezone suffix: `"2024-01-15T10:00:00"` (not `"2024-01-15T10:00:00Z"`)
2. **File Upload**: All POST endpoints require image file upload
3. **Form Data**: Send as multipart/form-data with two fields: `data` (JSON string) and `image` (file)
4. **Content-Type**: Use `multipart/form-data` when sending requests