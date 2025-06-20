from fileextract import extract_text_from_pdf, extract_section_only, split_into_sections, create_flat_text
from kmp import hitungLPS, KMP
from bm import *
from levenshtein import *
# Main usage
pdf_file = "../data/10674770.pdf"  # Ganti dengan path file PDF kamu
raw_text = extract_text_from_pdf(pdf_file)
# print(raw_text)
hasil = split_into_sections(raw_text)
section_name = "Experience"  # Ganti dengan nama section yang ingin diekstrak
sections = extract_section_only(pdf_file, section_name)
print(f"Extracted section '{section_name}':\n{sections}\n")
structured_sections = split_into_sections(raw_text)

# Format 1: Struktur rapi
for heading, content in structured_sections.items():
    print(f"{heading}\n{content}\n")

# Format 2: Flat text (tanpa kapitalisasi dan newline)
flat_version = create_flat_text(structured_sections)
print("\n" + "="*40 + "\nFLAT VERSION:\n")
print(flat_version)
# Simpan hasil struktur rapi
with open("output_structured.txt", "w", encoding="utf-8") as f:
    for heading, content in structured_sections.items():
        f.write(f"{heading}\n\n{content}\n\n")

# Simpan hasil versi flat (paragraf panjang lowercase)
with open("output_flat.txt", "w", encoding="utf-8") as f:
    f.write(flat_version)
hasil = KMP(flat_version, "view")
hasilbm = BM(flat_version, "view")
hasillevenshtein = levenshtein_search(flat_version, "view")
print(f"Jumlah kemunculan 'view' dalam teks metode BM: {hasilbm}")
print(f"Jumlah kemunculan 'view' dalam teks metode KMP: {hasil}")
print(f"Jumlah kemunculan 'view' dalam teks metode levenshtein: {hasillevenshtein}")