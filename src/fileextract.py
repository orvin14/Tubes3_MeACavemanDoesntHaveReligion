import fitz  # PyMuPDF

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


