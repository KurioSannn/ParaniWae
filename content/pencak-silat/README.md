# Konten Pencak Silat (draf riset)

Semua isi folder ini adalah **draf riset editorial** dan **belum divalidasi instruktur**. Folder ini bukan kurikulum
resmi perguruan mana pun.

| Folder | Isi |
|---|---|
| `catalog/common.json` | tradisi konten, partner editorial internal, blok keselamatan bersama (editorial), grup landmark |
| `movements/` | 43 dokumen gerakan (`mv.psdp.*`) dengan fase, anatomi, sumber, dan celah |
| `curricula/`, `lessons/` | 2 kursus, 9 modul, 16 pelajaran |
| `animations/` | 43 folder: 23 animasi SVG bergerak dan 20 `needs_reference`; `index.html` = pratinjau |
| `assessments/` | sengaja kosong: tidak ada penilaian AI benar/salah |

Data riset (sumber, katalog nasional, inventaris nama gerak) ada di `research/pencak-silat/`.

## Perintah

```bash
make content-validate          # validasi konten (ID, sumber, fase, animasi, kurikulum)
make animations                # bangun ulang SVG + pratinjau
make animations-validate       # validasi teknis aset
make animations-test           # tes generator/validator
make animations-browser-check  # bukti bergerak di Chromium nyata
make content-import            # DRY-RUN impor ke DB (draf); X=1 untuk eksekusi — backup DB dulu
```

Standar: `docs/MOVEMENT_CONTENT_STANDARD.md`, `docs/VECTOR_ANIMATION_SPEC.md`, `docs/CURRICULUM_STRUCTURE.md`,
`docs/CONTENT_PROVENANCE.md`, `docs/CONTENT_VALIDATION_STATUS.md`.
