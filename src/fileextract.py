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
def find_section_starts(text):
    section_patterns = {
        # Kunci adalah nama standar yang akan kita gunakan, value adalah pola regex
        "Summary": re.compile(r"^\s*(SUMMARY|OBJECTIVE|PROFILE|ABOUT\s+ME|RINGKASAN\s*(PRIBADI)?)\s*:?\s*$", re.IGNORECASE),
        "Experience": re.compile(r"^\s*(PROFESSIONAL\s+)?EXPERIENCE(S)?|WORK\s+HISTORY|PENGALAMAN\s*(KERJA)?\s*:?\s*$", re.IGNORECASE),
        "Education": re.compile(r"^\s*(EDUCATION|EDUCATION\s+AND\s+TRAINING|EDUCATION\s*&\s*TRAINING|ACADEMIC\s+(BACKGROUND|QUALIFICATIONS)|TRAINING|PENDIDIKAN|KUALIFIKASI\s*(AKADEMIK)?)\s*:?\s*$", re.IGNORECASE),
        "Skills": re.compile(r"^\s*(TECHNICAL\s+)?SKILLS|COMPETENCIES|PROFICIENCIES|KEMAMPUAN|KEAHLIAN\s*:?\s*$", re.IGNORECASE),
        "Projects": re.compile(r"^\s*(PROJECTS|PROYEK)\s*:?\s*$", re.IGNORECASE),
        "Awards": re.compile(r"^\s*(AWARDS|HONORS|PENGHARGAAN)\s*:?\s*$", re.IGNORECASE),
        "Certifications": re.compile(r"^\s*(CERTIFICATIONS|CERTIFICATES|SERTIFIKASI)\s*:?\s*$", re.IGNORECASE),
        "Accomplishments": re.compile(r"^\s*(ACCOMPLISHMENTS|ACHIEVEMENTS|PRESTASI)\s*:?\s*$", re.IGNORECASE),
        "Languages": re.compile(r"^\s*(LANGUAGES|BAHASA)\s*:?\s*$", re.IGNORECASE),
        "Interests": re.compile(r"^\s*(INTERESTS|MINAT)\s*:?\s*$", re.IGNORECASE),
        "Personal Information": re.compile(r"^\s*(PERSONAL\s+INFORMATION|INFORMASI\s+PRIBADI)\s*:?\s*$", re.IGNORECASE),
        "Additional Information": re.compile(r"^\s*(ADDITIONAL\s+INFORMATION|INFORMASI\s+TAMBAHAN|LAIN-LAIN)\s*:?\s*$", re.IGNORECASE),
    }
    
    found_sections = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        if not stripped_line: # Lewati baris kosong
            continue
            
        for section_name, pattern in section_patterns.items():
            match = pattern.match(stripped_line)
            if match:
                remaining_text_after_heading = stripped_line[match.end():].strip()
                if len(remaining_text_after_heading) < 20 : # Judul biasanya tidak diikuti banyak teks
                    found_sections.append({'index': i, 'name': section_name, 'line_text': lines[i]}) # Simpan baris asli
                    break 
    
    found_sections.sort(key=lambda x: x['index']) # Urutkan berdasarkan urutan kemunculan di CV
    return found_sections

def split_into_sections(text):
    if not text or not text.strip():
        return {}
        
    lines = text.splitlines()
    section_starts = find_section_starts(text)
    
    sections = {}
    num_lines = len(lines)
    
    for i, start_info in enumerate(section_starts):
        current_heading_name = start_info['name']
        # Baris konten dimulai dari baris SETELAH judul
        content_start_line_index = start_info['index'] + 1
    
        if i + 1 < len(section_starts):
            content_end_line_index = section_starts[i+1]['index']
        else:
            content_end_line_index = num_lines
            
        section_content_lines = lines[content_start_line_index : content_end_line_index]
        sections[current_heading_name] = "\n".join(section_content_lines).strip() # Hilangkan spasi ekstra di awal/akhir blok
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

def is_potential_entry_start(line_text, next_line_text, year_pattern):
    stripped_line = line_text.strip()
    if not stripped_line or stripped_line.startswith(('-', '*', '•', '#', 'o ')): # Abaikan bullet points umum
        return False

    # Kasus 1: Baris saat ini mengandung tahun (dan bukan bullet point)
    if year_pattern.search(stripped_line):
        return True 
        
    # Kasus 2: Baris saat ini adalah kandidat judul (pendek, bukan bullet), dan baris BERIKUTNYA mengandung tahun (dan bukan bullet point).
    if next_line_text:
        stripped_next_line = next_line_text.strip()
        if year_pattern.search(stripped_next_line) and \
           not stripped_next_line.startswith(('-', '*', '•', '#', 'o ')):
            # Periksa apakah baris saat ini terlihat seperti judul (misalnya, tidak terlalu panjang)
            if len(stripped_line.split()) < 7:
                return True
    return False

def parse_experience_section(experience_block_text):
    parsed_entries = []
    if not experience_block_text or not experience_block_text.strip() or \
       "not found" in experience_block_text.lower():
        return parsed_entries

    lines = experience_block_text.strip().split('\n')
    year_pattern = re.compile(r'\b\d{4}\b') # Pola untuk 4 digit tahun
    
    current_entry_lines = []
    
    for i in range(len(lines)):
        current_line_text = lines[i]
        next_line_text = lines[i+1] if i + 1 < len(lines) else None
        
        # Cek apakah baris saat ini menandakan awal entri baru
        if is_potential_entry_start(current_line_text, next_line_text, year_pattern):
            if current_entry_lines: # Jika ada baris terkumpul dari entri sebelumnya
                entry_text_block = "\n".join(current_entry_lines).strip()
                if entry_text_block:
                    entry_lines_for_parsing = entry_text_block.split('\n')
                    title = entry_lines_for_parsing[0].strip()
                    details = "\n".join(entry_lines_for_parsing[1:]).strip()
                    parsed_entries.append({'title': title, 'details': details})
                current_entry_lines = [] # Mulai buffer baru untuk entri ini
        
        if current_line_text.strip(): # Hanya tambahkan baris yang tidak kosong (atau kosong jika sudah di tengah entri)
             current_entry_lines.append(current_line_text) # Simpan baris asli untuk menjaga format

    # Tambahkan entri terakhir yang terkumpul
    if current_entry_lines:
        entry_text_block = "\n".join(current_entry_lines).strip()
        if entry_text_block:
            entry_lines_for_parsing = entry_text_block.split('\n')
            title = entry_lines_for_parsing[0].strip()
            details = "\n".join(entry_lines_for_parsing[1:]).strip()
            parsed_entries.append({'title': title, 'details': details})

    return parsed_entries

def parse_education_section(education_block_text):
    parsed_entries = []
    if not education_block_text or not education_block_text.strip() or \
       "not found" in education_block_text.lower():
        return parsed_entries

    lines = education_block_text.strip().split('\n')
    year_pattern = re.compile(r'\b\d{4}\b')
    
    current_entry_lines = []

    for i in range(len(lines)):
        current_line_text = lines[i]
        next_line_text = lines[i+1] if i + 1 < len(lines) else None
        
        if is_potential_entry_start(current_line_text, next_line_text, year_pattern):
            if current_entry_lines:
                entry_text_block = "\n".join(current_entry_lines).strip()
                if entry_text_block:
                    entry_lines_for_parsing = entry_text_block.split('\n')
                    main_info = entry_lines_for_parsing[0].strip() 
                    details = "\n".join(entry_lines_for_parsing[1:]).strip()
                    parsed_entries.append({'main_info': main_info, 'details': details})
                current_entry_lines = []
        
        if current_line_text.strip():
            current_entry_lines.append(current_line_text)

    if current_entry_lines:
        entry_text_block = "\n".join(current_entry_lines).strip()
        if entry_text_block:
            entry_lines_for_parsing = entry_text_block.split('\n')
            main_info = entry_lines_for_parsing[0].strip()
            details = "\n".join(entry_lines_for_parsing[1:]).strip()
            parsed_entries.append({'main_info': main_info, 'details': details})
            
    return parsed_entries

def parse_skills_section(skills_text_block):
    skills = []
    if not skills_text_block or not skills_text_block.strip() or \
       "not found" in skills_text_block.lower():
        return skills
    normalized_text = re.sub(r"^\s*[-*•–✔]\s+", "", skills_text_block, flags=re.MULTILINE)
    normalized_text = re.sub(r"\s*;\s*", ",", normalized_text) 
    
    lines = normalized_text.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = re.split(r":\s+", line, maxsplit=1)
        text_to_parse_for_skills = parts[-1] # Ambil bagian terakhir

        # Pisahkan berdasarkan koma
        potential_skills = re.split(r",\s*", text_to_parse_for_skills)
        for skill in potential_skills:
            skill = skill.strip().rstrip('.') # Hapus spasi dan titik di akhir
            if skill and len(skill) > 1: # Hindari string kosong atau karakter tunggal
                if not (":" in skill and len(skill.split()) < 4): 
                    skills.append(skill)
    
    unique_skills = sorted(list(set(s for s in skills if s)), key=lambda s: s.lower()) # Urutkan agar konsisten
    return unique_skills