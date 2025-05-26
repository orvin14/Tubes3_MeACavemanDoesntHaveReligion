import fitz  # PyMuPDF
import re

# Fungsi untuk membaca isi file PDF
def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Fungsi untuk memisahkan bagian berdasarkan heading
def split_into_sections(text):
    # Heading yang diharapkan
    headings = [
        "Skills", "Summary", "Highlights", "Accomplishments",
        "Experience", "Education"
    ]

    sections = {}
    current_heading = None
    buffer = []

    lines = text.splitlines()
    for line in lines:
        stripped_line = line.strip()
        if stripped_line in headings:
            if current_heading:
                sections[current_heading] = "\n".join(buffer).strip()
                buffer = []
            current_heading = stripped_line
        elif current_heading:
            buffer.append(stripped_line)

    # Menambahkan bagian terakhir
    if current_heading:
        sections[current_heading] = "\n".join(buffer).strip()

    return sections

# Fungsi untuk membuat format paragraf (versi flat, lowercase)
def create_flat_text(sections_dict):
    flat_text = []
    for heading, content in sections_dict.items():
        content_flat = content.replace("\n", " ").replace("•", "")
        flat_text.append(f"{heading.lower()} {content_flat.lower()}")
    return " ".join(flat_text)

def extract_section_only(file_path, section_name):
    raw_text = extract_text_from_pdf(file_path)
    sections = split_into_sections(raw_text)
    return sections.get(section_name, f"{section_name} section not found.")

# Main usage
pdf_file = "../data/10005171.pdf"  # Ganti dengan path file PDF kamu
raw_text = extract_text_from_pdf(pdf_file)
section_name = "Experience"  # Ganti dengan nama section yang ingin diekstrak
sections = extract_section_only(pdf_file, section_name)
print(f"Extracted section '{section_name}':\n{sections}\n")
structured_sections = split_into_sections(raw_text)

# Format 1: Struktur rapi
for heading, content in structured_sections.items():
    print(f"{heading}\n\n{content}\n")

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

