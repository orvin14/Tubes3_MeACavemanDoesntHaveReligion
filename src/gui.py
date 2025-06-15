import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
import mysql.connector
import os
import time
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


try:
    from fileextract import extract_text_from_pdf, split_into_sections, create_flat_text, parse_education_section, parse_experience_section, parse_skills_section
    from kmp import KMP
    from ahocorasick import AhoCorasick
    from encrypt import xor_decrypt_data, get_profile_by_id, ENCRYPTION_KEY, get_db_connection
    from bm import BM
    from levenshtein import levenshteinDistance, levenshteinSearchWithMatchedWords, dynamicLevenshteinSearch
except ImportError as e:
    messagebox.showerror("Import Error", f"Tidak dapat mengimpor modul yang dibutuhkan: {e}\nPastikan fileextract.py dan kmp.py ada.")
    sys.exit(1)


class CVAnalyzerApp:
    def __init__(self, master):
        self.master = master
        master.title("CV Analyzer App")
        master.geometry("850x750")
        master.configure(bg="#f0f0f0")

        title_font = ("Arial", 18, "bold")
        label_font = ("Arial", 10)
        button_font = ("Arial", 10, "bold")
        results_title_font = ("Arial", 14, "bold")

        main_frame = ttk.Frame(master, padding="20 20 20 20", style="Main.TFrame")
        main_frame.pack(expand=True, fill="both")
        ttk.Style().configure("Main.TFrame", background="#f0f0f0")

        title_label = ttk.Label(main_frame, text="CV Analyzer App", font=title_font, background="#f0f0f0")
        title_label.pack(pady=(0, 20))

        input_frame = ttk.Frame(main_frame, style="Input.TFrame")
        input_frame.pack(fill="x", pady=(0,15))
        ttk.Style().configure("Input.TFrame", background="#f0f0f0")

        keywords_label = ttk.Label(input_frame, text="Keywords:", font=label_font, background="#f0f0f0")
        keywords_label.grid(row=0, column=0, padx=(0,10), pady=5, sticky="w")
        self.keywords_entry = ttk.Entry(input_frame, width=60, font=label_font)
        self.keywords_entry.grid(row=0, column=1, columnspan=5, padx=5, pady=5, sticky="ew")
        self.keywords_entry.insert(0, "React, Express, HTML")

        algo_label = ttk.Label(input_frame, text="Search Algorithm:", font=label_font, background="#f0f0f0")
        algo_label.grid(row=1, column=0, padx=(0,10), pady=5, sticky="w")
        
        algo_options_frame = ttk.Frame(input_frame, style="Input.TFrame")
        algo_options_frame.grid(row=1, column=1, columnspan=3, sticky="w")
        self.search_algo_var = tk.StringVar(value="KMP")
        # self.search_algo_var.trace_add("write", self.toggle_levenshtein_threshold)

        kmp_radio = ttk.Radiobutton(algo_options_frame, text="KMP", variable=self.search_algo_var, value="KMP", style="TRadiobutton")
        kmp_radio.pack(side="left", padx=(0, 10))
        bm_radio = ttk.Radiobutton(algo_options_frame, text="BM", variable=self.search_algo_var, value="BM", style="TRadiobutton")
        bm_radio.pack(side="left")
        ahoc_radio = ttk.Radiobutton(algo_options_frame, text="Aho-Corasick", variable=self.search_algo_var, value="Aho-Corasick", style="TRadiobutton")
        ahoc_radio.pack(side="left", padx=(10, 0))
        ttk.Style().configure("TRadiobutton", background="#f0f0f0", font=label_font)


        top_matches_label = ttk.Label(input_frame, text="Top Matches:", font=label_font, background="#f0f0f0")
        top_matches_label.grid(row=2, column=0, padx=(0,10), pady=5, sticky="w") 
        self.top_matches_spinbox = ttk.Spinbox(input_frame, from_=1, to=20, width=5, font=label_font)
        self.top_matches_spinbox.grid(row=2, column=1, padx=5, pady=5, sticky="w") 
        self.top_matches_spinbox.set("3")

        self.use_encryption_var = tk.BooleanVar(value=True)
        encrypt_check = ttk.Checkbutton(
            input_frame, 
            text="Database Terenkripsi", 
            variable=self.use_encryption_var, 
            style="TRadiobutton"
        )
        encrypt_check.grid(row=3, column=0, columnspan=2, padx=0, pady=5, sticky="w") 
        input_frame.columnconfigure(1, weight=1)


        search_button = ttk.Button(main_frame, text="Search", command=self.perform_search, style="Search.TButton")
        search_button.pack(fill="x", pady=(10, 20))
        ttk.Style().configure("Search.TButton", font=button_font, padding="10")

        results_frame_container = ttk.Frame(main_frame, style="Results.TFrame")
        results_frame_container.pack(expand=True, fill="both")
        ttk.Style().configure("Results.TFrame", background="#f0f0f0")

        top_info_frame = ttk.Frame(results_frame_container, style="Results.TFrame")
        top_info_frame.pack(side="top", fill="x", pady=(0, 5))

        results_title_label = ttk.Label(top_info_frame, text="Results", font=results_title_font, background="#f0f0f0")
        results_title_label.pack(pady=(0,5))
        self.scan_info_label = ttk.Label(top_info_frame, text="", font=label_font, background="#f0f0f0")
        
        self.results_canvas = tk.Canvas(results_frame_container, borderwidth=0, background="#e0e0e0")
        self.scrollbar_y = ttk.Scrollbar(results_frame_container, orient="vertical", command=self.results_canvas.yview)
        self.results_canvas.configure(yscrollcommand=self.scrollbar_y.set)
        self.scrollbar_y.pack(side="right", fill="y") 
        self.results_canvas.pack(side="left", fill="both", expand=True)
        self.scrollable_card_frame = ttk.Frame(self.results_canvas, style="ResultsDisplay.TFrame")
        ttk.Style().configure("ResultsDisplay.TFrame", background="#e0e0e0")
        self.results_canvas.create_window((0, 0), window=self.scrollable_card_frame, anchor="nw", tags="self.scrollable_card_frame")
        self.scrollable_card_frame.bind("<Configure>", self.on_frame_configure)
        self.results_canvas.bind("<Configure>", self.on_canvas_configure)

    def on_frame_configure(self, event=None):
        """Update scrollregion canvas agar sesuai dengan ukuran konten."""
        self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        canvas_width = event.width
        self.results_canvas.itemconfig("self.scrollable_card_frame", width=canvas_width)

    def process_cv_worker(db_row_data, parsed_keywords_list, algorithm_choice, aho_automaton_instance=None, levenshtein_threshold=0):
        cv_path_from_db, first_name, last_name, applicant_id = db_row_data
        candidate_name = f"{first_name} {last_name}"
        
        if not cv_path_from_db: return None
        actual_cv_path = os.path.abspath(os.path.join(SCRIPT_DIR, cv_path_from_db))
        if not os.path.exists(actual_cv_path): return None
        
        try:
            raw_text = extract_text_from_pdf(actual_cv_path)
            if not raw_text: return None
            
            structured_sections = split_into_sections(raw_text)
            flat_text = create_flat_text(structured_sections).lower()
            if not flat_text: return None

            current_cv_matched_keywords_details = []
            current_cv_total_matches = 0
            total_exact_duration_s = 0.0
            total_fuzzy_duration_s = 0.0
            
            # === PERUBAHAN 1: Tambahkan flag untuk melacak exact match ===
            has_exact_match = False

            if algorithm_choice == "Aho-Corasick":
                if aho_automaton_instance:
                    start_time = time.time()
                    per_keyword_counts = aho_automaton_instance.search(flat_text)
                    end_time = time.time()
                    total_exact_duration_s = end_time - start_time
                    
                    for keyword, count in per_keyword_counts.items():
                        if count > 0:
                            has_exact_match = True # Aho-Corasick adalah exact match
                            current_cv_matched_keywords_details.append(f"{keyword.capitalize()}: {count} occurrence{'s' if count > 1 else ''}")
                            current_cv_total_matches += count
            else:
                for keyword_pattern in parsed_keywords_list:
                    count = 0
                    
                    start_exact = time.time()
                    if algorithm_choice == "KMP": 
                        count = KMP(flat_text, keyword_pattern) 
                    elif algorithm_choice == "BM": 
                        count = BM(flat_text, keyword_pattern)
                    end_exact = time.time()
                    total_exact_duration_s += (end_exact - start_exact)

                    if count > 0:
                        has_exact_match = True # Tandai bahwa kita menemukan exact match
                        details_string = f"{keyword_pattern.capitalize()}: {count} occurrence{'s' if count > 1 else ''}"
                        current_cv_matched_keywords_details.append(details_string)
                        current_cv_total_matches += count
                    elif count == 0:
                        start_fuzzy = time.time()
                        fuzzy_count, matched_words = dynamicLevenshteinSearch(flat_text, keyword_pattern)
                        end_fuzzy = time.time()
                        total_fuzzy_duration_s += (end_fuzzy - start_fuzzy)
                        
                        if fuzzy_count > 0:
                            details_string = f"{keyword_pattern.capitalize()} (fuzzy): {fuzzy_count} occurrence{'s' if fuzzy_count > 1 else ''}"
                            if matched_words:
                                unique_matched_display = sorted(list(set(matched_words)))
                                details_string += f" (kata cocok: {', '.join(unique_matched_display)})"
                            current_cv_matched_keywords_details.append(details_string)
                            current_cv_total_matches += fuzzy_count
                    
            if current_cv_total_matches > 0:
                # Prioritas 1 untuk CV dengan exact match (akan muncul di atas)
                # Prioritas 2 untuk CV yang hanya punya fuzzy match
                match_priority = 1 if has_exact_match else 2

                return {
                    "id": applicant_id, "name": candidate_name, 
                    "total_matches": current_cv_total_matches,
                    "matched_keywords": current_cv_matched_keywords_details, 
                    "cv_path": cv_path_from_db,
                    "exact_duration_s": total_exact_duration_s,
                    "fuzzy_duration_s": total_fuzzy_duration_s,
                    "match_priority": match_priority # Tambahkan label ke hasil
                }
            return None
        except Exception as e:
            print(f"Error processing CV {actual_cv_path} (ID: {applicant_id}) in worker: {e}")
            return None

    def perform_search(self):
        keywords_str = self.keywords_entry.get()
        algorithm = self.search_algo_var.get()
        use_encryption = self.use_encryption_var.get()
        
        try:
            top_n = int(self.top_matches_spinbox.get())
        except ValueError:
            messagebox.showerror("Input Error", "Top Matches must be a number.")
            return

        if not keywords_str:
            messagebox.showwarning("Input Error", "Keywords cannot be empty.")
            return

        parsed_keywords = [k.strip().lower() for k in keywords_str.split(',') if k.strip()]
        if not parsed_keywords:
            messagebox.showwarning("Input Error", "No valid keywords entered.")
            return

        all_cv_results = []
        conn = None
        num_cvs_from_db = 0
        start_time = time.time()
        
        total_exact_search_duration_s = 0.0
        total_fuzzy_search_duration_s = 0.0

        main_aho_automaton = None
        if algorithm == "Aho-Corasick":
            if not parsed_keywords:
                messagebox.showwarning("Input Error", "No valid keywords entered for Aho-Corasick.")
                return
            main_aho_automaton = AhoCorasick(parsed_keywords)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            query = "SELECT cv_path, first_name, last_name, ad.applicant_id FROM applicationdetail ad JOIN applicantprofile ap ON ap.applicant_id=ad.applicant_id;"
            cursor.execute(query)
            db_rows = cursor.fetchall()
            db_rows_decrypted = []
            for row in db_rows:
                cv_path_value, first_name_value, last_name_value, applicant_id_value = row
                if use_encryption:
                    first_name_value = xor_decrypt_data(first_name_value, ENCRYPTION_KEY)
                    last_name_value = xor_decrypt_data(last_name_value, ENCRYPTION_KEY)
                db_rows_decrypted.append((cv_path_value, first_name_value, last_name_value, applicant_id_value))
            num_cvs_from_db = len(db_rows_decrypted)

            if not db_rows_decrypted:
                messagebox.showinfo("Info", "No CV data found in the database.")
                if hasattr(self, 'scan_info_label'):
                    self.scan_info_label.config(text="No CVs to process.")
                return
            
            num_workers = (os.cpu_count() or 2) * 2 
            
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(CVAnalyzerApp.process_cv_worker, db_row, parsed_keywords, algorithm, main_aho_automaton) for db_row in db_rows_decrypted]
                
                for future_result in as_completed(futures):
                    try:
                        result = future_result.result() 
                        if result:
                            all_cv_results.append(result)
                            total_exact_search_duration_s += result.get("exact_duration_s", 0)
                            total_fuzzy_search_duration_s += result.get("fuzzy_duration_s", 0)
                    except Exception as e_thread:
                        print(f"Error retrieving result from a worker thread: {e_thread}")
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"MySQL Error: {err}")
            return
        except Exception as e_main: 
            messagebox.showerror("Processing Error", f"An unexpected error occurred: {e_main}")
            return
        finally:
            if conn and conn.is_connected():
                if 'cursor' in locals() and cursor: cursor.close()
                conn.close()

        all_cv_results.sort(key=lambda x: (x.get('match_priority', 2), -x['total_matches']))
        top_results_to_display = all_cv_results[:top_n]
        end_time = time.time()
        
        total_processing_time_ms = round((end_time - start_time) * 1000)
        total_exact_search_time_ms = round(total_exact_search_duration_s * 1000)
        total_fuzzy_search_time_ms = round(total_fuzzy_search_duration_s * 1000)

        if hasattr(self, 'scan_info_label'):
            info_text = f"{num_cvs_from_db} CVs processed, found {len(all_cv_results)} matches. Total time: {total_processing_time_ms}ms"
            
            breakdown_text = f"\nBreakdown: Exact Time: {total_exact_search_time_ms}ms"
            if total_fuzzy_search_time_ms > 0:
                breakdown_text += f" | Fuzzy Time: {total_fuzzy_search_time_ms}ms"
            info_text += breakdown_text
            
            self.scan_info_label.config(text=info_text)
            self.scan_info_label.pack(pady=(0,5)) 

        if hasattr(self, 'display_results'):
            self.display_results(top_results_to_display)

    def display_results(self, results_data):
        for widget in self.scrollable_card_frame.winfo_children():
            widget.destroy()

        if not results_data:
            no_results_label = ttk.Label(self.scrollable_card_frame, text="No results to display.", font=("Arial", 10), background="#e0e0e0")
            no_results_label.pack(pady=20)
            self.scrollable_card_frame.update_idletasks()
            self.on_frame_configure()
            return
        
        max_cols = 3 
        for i, result_item_data in enumerate(results_data):
            row = i // max_cols
            col = i % max_cols

            card = ttk.Frame(self.scrollable_card_frame, padding="10", relief="solid", borderwidth=1, style="Card.TFrame")
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.scrollable_card_frame.grid_columnconfigure(col, weight=1)

            ttk.Style().configure("Card.TFrame", background="#ffffff")
            text_content_frame = ttk.Frame(card, style="Card.TFrame")
            text_content_frame.pack(side="top", fill="both", expand=True) 

            name_label = ttk.Label(text_content_frame, text=result_item_data["name"], font=("Arial", 12, "bold"), background="#ffffff")
            name_label.pack(anchor="w", pady=(0,2))

            matches_count = result_item_data['total_matches']
            priority = result_item_data.get('match_priority', 2)
            
            match_type_indicator = ""
            if priority == 1:
                match_type_indicator = "(Exact)"
            elif priority == 2:
                match_type_indicator = "(Fuzzy Only)"

            matches_text = f"{matches_count} match{'es' if matches_count != 1 else ''} {match_type_indicator}"
            matches_label = ttk.Label(text_content_frame, text=matches_text, font=("Arial", 9, "italic"), background="#ffffff")
            matches_label.pack(anchor="w", pady=(0,5))

            ttk.Label(text_content_frame, text="Matched keywords:", font=("Arial", 9, "underline"), background="#ffffff").pack(anchor="w", pady=(5,2))
            for idx, detail in enumerate(result_item_data["matched_keywords"]):
                detail_label = ttk.Label(text_content_frame, text=f"{idx+1}. {detail}", font=("Arial", 9), background="#ffffff")
                detail_label.pack(anchor="w")
            
            buttons_frame = ttk.Frame(card, style="Card.TFrame") 
            buttons_frame.pack(side="bottom", fill="x", pady=(10,0))

            summary_button = ttk.Button(buttons_frame, text="Summary", command=lambda data=result_item_data: self.view_summary(data), style="CardButton.TButton", width=10)
            summary_button.pack(side="left", padx=(0,5))

            view_cv_button = ttk.Button(buttons_frame, text="View CV", command=lambda data=result_item_data: self.view_cv(data), style="CardButton.TButton", width=10)
            view_cv_button.pack(side="right", padx=(5,0))

            ttk.Style().configure("CardButton.TButton", font=("Arial", 8))
        
        self.scrollable_card_frame.update_idletasks()
        self.on_frame_configure()

    def view_summary(self, result_data):
        cv_path_from_db = result_data.get('cv_path')
        candidate_name = result_data.get('name')
        applicant_id = result_data.get('id') 

        if not cv_path_from_db:
            messagebox.showerror("Error", "CV path not available for summary.")
            return

        actual_cv_path = os.path.abspath(os.path.join(SCRIPT_DIR, cv_path_from_db))
        if not os.path.exists(actual_cv_path):
            messagebox.showerror("Error", f"CV file not found at: {actual_cv_path}")
            return
        perlu_decrypt = self.use_encryption_var.get()
        biodata = {"name": candidate_name, "birthdate": "N/A", "address": "N/A", "phone": "N/A"}
        try:
            profile = get_profile_by_id(applicant_id, decrypt=perlu_decrypt)
            if profile:
                birthdate_db = profile.get('date_of_birth')
                if birthdate_db:
                    try:
                        biodata['birthdate'] = birthdate_db
                    except AttributeError:
                        biodata['birthdate'] = str(birthdate_db)
                biodata['address'] = profile.get('address', "N/A")
                biodata['phone'] = profile.get('phone_number', "N/A")
        except mysql.connector.Error as err:
            print(f"Database error fetching profile for {candidate_name}: {err}")
            messagebox.showwarning("Database Info", f"Could not fetch detailed biodata for {candidate_name}.")

        parsed_skills_list = []
        parsed_experience_entries = []
        parsed_education_entries = []
        
        try:
            full_cv_text = extract_text_from_pdf(actual_cv_path)
            if full_cv_text:
                all_sections = split_into_sections(full_cv_text) 
                
                skills_block = all_sections.get("Skills", "")
                experience_block = all_sections.get("Experience", "")
                education_block = all_sections.get("Education", "")

                parsed_skills_list = parse_skills_section(skills_block)
                parsed_experience_entries = parse_experience_section(experience_block)
                parsed_education_entries = parse_education_section(education_block)
            else:
                messagebox.showwarning("CV Info", "Could not extract any text from the CV PDF.")
                # Set ke list kosong jika teks tidak bisa diekstrak

        except Exception as e_extract:
            messagebox.showerror("Extraction Error", f"Could not parse sections from CV: {e_extract}")

        SummaryWindow(self.master, 
                      title=f"CV Summary: {candidate_name}",
                      biodata=biodata,
                      skills_list=parsed_skills_list,
                      experience_entries=parsed_experience_entries,
                      education_entries=parsed_education_entries)


    def view_cv(self, result_data):
        path_from_db = result_data.get('cv_path')
        if path_from_db:
            cv_path_to_use = os.path.abspath(os.path.join(SCRIPT_DIR, path_from_db))
            if os.path.exists(cv_path_to_use):
                try:
                    if sys.platform == "win32": os.startfile(cv_path_to_use)
                    elif sys.platform == "darwin": subprocess.call(["open", cv_path_to_use])
                    else: subprocess.call(["xdg-open", cv_path_to_use])
                except Exception as e:
                    messagebox.showerror("View CV Error", f"Tidak dapat membuka file: {cv_path_to_use}\nError: {e}")
            else:
                 messagebox.showwarning("View CV", f"File CV tidak ditemukan di: {cv_path_to_use}")
        else:
            messagebox.showwarning("View CV", f"Path CV tidak tersedia untuk {result_data['name']}.")

class SummaryWindow(Toplevel):
    def __init__(self, parent, title, biodata, 
                 skills_list,           
                 experience_entries,   
                 education_entries,   
                 **kwargs):
        super().__init__(parent, **kwargs)
        self.title(title)
        self.geometry("700x650") 
        self.configure(bg="#e0e0e0")

        # Font Styles
        self.title_font = ("Arial", 16, "bold")
        self.heading_font = ("Arial", 12, "bold")
        self.sub_heading_font = ("Arial", 10, "bold")
        self.content_font = ("Arial", 10)
        self.content_font_bold = ("Arial", 10, "bold")
        self.tag_font = ("Arial", 9)

        # Warna
        self.section_bg = "#f0f0f0" 
        self.heading_section_bg = "#6c757d" 
        self.heading_text_color = "white"
        self.tag_bg = "#898D92" 
        self.tag_fg = "#FFFFFF"

        self.tag_text_padx = 6
        self.tag_text_pady = 2

        # Jarak antar tag
        self.tag_outer_padx = 3
        self.tag_outer_pady = 3
        self.tag_relief = "raised"
        self.tag_borderwidth = 1

        main_canvas = tk.Canvas(self, borderwidth=0, background="#e0e0e0")
        scrollbar_y = ttk.Scrollbar(self, orient="vertical", command=main_canvas.yview)
        main_canvas.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.pack(side="right", fill="y")
        main_canvas.pack(side="left", fill="both", expand=True)

        content_frame = ttk.Frame(main_canvas, padding="20", style="Content.TFrame")
        ttk.Style().configure("Content.TFrame", background="#e0e0e0")
        main_canvas.create_window((0,0), window=content_frame, anchor="nw", tags="content_frame")
        content_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.bind("<Configure>", lambda e: main_canvas.itemconfig("content_frame", width=e.width))

        win_title_label = ttk.Label(content_frame, text="CV Summary", font=self.title_font, background="#e0e0e0", anchor="center")
        win_title_label.pack(pady=(0, 20), fill="x")

        self._create_biodata_section(content_frame, biodata)
        self._create_skills_section(content_frame, "Skills:", skills_list)
        self._create_experience_section(content_frame, "Job History:", experience_entries) 
        self._create_education_section(content_frame, "Education:", education_entries) 

        self.transient(parent)
        self.grab_set()
        self.focus_set()

    def _create_biodata_section(self, parent_frame, biodata):
        header_frame = tk.Frame(parent_frame, bg=self.heading_section_bg)
        header_frame.pack(fill="x", pady=(10,0))
        name_label = tk.Label(header_frame, text=biodata.get("name", "N/A"), font=self.heading_font, 
                              bg=self.heading_section_bg, fg=self.heading_text_color, padx=10, pady=5)
        name_label.pack(anchor="w")
        detail_frame = tk.Frame(parent_frame, bg=self.section_bg, padx=10, pady=10)
        detail_frame.pack(fill="x", pady=(0,15))
        ttk.Label(detail_frame, text=f"Birthdate: {biodata.get('birthdate', 'N/A')}", font=self.content_font, background=self.section_bg).pack(anchor="w")
        ttk.Label(detail_frame, text=f"Address: {biodata.get('address', 'N/A')}", font=self.content_font, background=self.section_bg).pack(anchor="w")
        ttk.Label(detail_frame, text=f"Phone: {biodata.get('phone', 'N/A')}", font=self.content_font, background=self.section_bg).pack(anchor="w")


    def _create_skills_section(self, parent_frame_for_section_title, section_title_text, skills_list_data):
        section_title_label = ttk.Label(parent_frame_for_section_title, text=section_title_text, 
                                        font=self.heading_font, background="#e0e0e0")
        section_title_label.pack(anchor="w", pady=(10,2), fill="x")
        
        self.skills_display_area = tk.Frame(parent_frame_for_section_title, bg=self.section_bg, padx=10, pady=10)
        self.skills_display_area.pack(fill="x", pady=(0,15))

        if not skills_list_data:
            ttk.Label(self.skills_display_area, text="Not available.", 
                      font=self.content_font, background=self.section_bg).pack(anchor="w")
            return

        self._skills_list_for_redraw = skills_list_data
        
        # Inisialisasi atribut untuk ukuran tag jika belum ada
        if not hasattr(self, '_uniform_tag_width_calculated'):
            self._uniform_tag_width_calculated = False
            self._uniform_tag_width = 0
            self._uniform_tag_height = 0
        
        self.skills_display_area.bind("<Configure>", self._redraw_skill_tags_grid)

        self.after(10, self._redraw_skill_tags_grid) 


    def _calculate_uniform_tag_size(self):
        if not hasattr(self, '_skills_list_for_redraw') or not self._skills_list_for_redraw: # Pengecekan tambahan
            print("Warning: _skills_list_for_redraw tidak ada atau kosong saat _calculate_uniform_tag_size.")
            self._uniform_tag_width = 70 
            self._uniform_tag_height = 25
            self._uniform_tag_width_calculated = True
            return False

        longest_skill_text = max(self._skills_list_for_redraw, key=len, default="")
        if not longest_skill_text:
            print("Warning: Tidak ada teks skill terpanjang untuk diukur.")
            self._uniform_tag_width = 70 
            self._uniform_tag_height = 25
            self._uniform_tag_width_calculated = True
            return False

        try:
            dummy_text_label = tk.Label(self, text=longest_skill_text, font=self.tag_font,
                                        padx=self.tag_text_padx, pady=self.tag_text_pady)
            dummy_text_label.update_idletasks() 
            
            req_width = dummy_text_label.winfo_reqwidth()
            req_height = dummy_text_label.winfo_reqheight()
            dummy_text_label.destroy()
        except tk.TclError as e:
            print(f"Error saat membuat/mengukur dummy_text_label: {e}")
            req_width = 0
            req_height = 0

        if req_width > 1 and req_height > 1:
            self._uniform_tag_width = req_width
            self._uniform_tag_height = req_height
            self._uniform_tag_width_calculated = True
            return True
        else:
            print(f"Warning: Pengukuran tag skill gagal (W={req_width}, H={req_height}), menggunakan ukuran fallback.")
            self._uniform_tag_width = 70 
            self._uniform_tag_height = 25
            self._uniform_tag_width_calculated = True # Tandai sudah dihitung 
            return False


    def _redraw_skill_tags_grid(self, event=None):
        if not self.winfo_exists():
            return

        for widget in self.skills_display_area.winfo_children():
            widget.destroy()

        if not hasattr(self, '_skills_list_for_redraw') or not self._skills_list_for_redraw:
            ttk.Label(self.skills_display_area, text="Not available.", 
                      font=self.content_font, background=self.section_bg).pack(anchor="w")
            return

        if not self._uniform_tag_width_calculated:
            self._calculate_uniform_tag_size() 
            if self._uniform_tag_width <= 1 or self._uniform_tag_height <= 1 :
                 self._uniform_tag_width = 70
                 self._uniform_tag_height = 20

        container_width = self.skills_display_area.winfo_width()
        if container_width <= 1: 
            return

        effective_tag_width = self._uniform_tag_width + (self.tag_outer_padx * 2)
        if effective_tag_width <= 0: effective_tag_width = 75 # Penjagaan tambahan
        num_cols = max(1, container_width // effective_tag_width)

        current_row = 0
        current_col = 0
        for skill_name in self._skills_list_for_redraw:
            tag_frame = tk.Frame(self.skills_display_area, 
                                 width=self._uniform_tag_width, 
                                 height=self._uniform_tag_height,
                                 bg=self.tag_bg, 
                                 relief=self.tag_relief, 
                                 borderwidth=self.tag_borderwidth)
            tag_frame.pack_propagate(False)

            tag_text_label = tk.Label(tag_frame, text=skill_name, font=self.tag_font,
                                      bg=self.tag_bg, fg=self.tag_fg, anchor="center")
            tag_text_label.pack(expand=True, fill="both", padx=self.tag_text_padx, pady=self.tag_text_pady)
            
            tag_frame.grid(row=current_row, column=current_col, 
                           padx=self.tag_outer_padx, pady=self.tag_outer_pady, sticky="nw")

            current_col += 1
            if current_col >= num_cols:
                current_col = 0
                current_row += 1

    def _create_experience_section(self, parent_frame, section_title_text, experience_entries):
        section_title_label = ttk.Label(parent_frame, text=section_title_text, font=self.heading_font,
                                        background="#e0e0e0")
        section_title_label.pack(anchor="w", pady=(15, 5), fill="x")

        experience_entries_container = tk.Frame(parent_frame, bg=self.section_bg, padx=10, pady=0)
        experience_entries_container.pack(fill="x", pady=(0, 15))

        if not experience_entries:
            ttk.Label(experience_entries_container, text="Not available.",
                      font=self.content_font, background=self.section_bg).pack(anchor="w", fill="x", padx=0, pady=10)
            return

        for job_entry in experience_entries:
            job_title_text = job_entry.get('title', 'N/A')
            job_details_text = job_entry.get('details', '')

            entry_item_frame = tk.Frame(experience_entries_container, bg=self.section_bg)
            entry_item_frame.pack(fill="x", pady=(0, 10))

            job_title_header_frame = tk.Frame(entry_item_frame, bg=self.heading_section_bg)
            job_title_header_frame.pack(fill="x")
            actual_title_label = tk.Label(job_title_header_frame, text=job_title_text,
                                           font=self.content_font_bold,
                                           bg=self.heading_section_bg, fg=self.heading_text_color,
                                           padx=10, pady=4, anchor="w", justify="left")
            actual_title_label.pack(fill="x")

            if job_details_text:
                details_content_frame = tk.Frame(entry_item_frame, bg=self.section_bg, padx=0) 
                details_content_frame.pack(fill="x", expand=True) 
                
                details_label = ttk.Label(details_content_frame, text=job_details_text,
                                          font=self.content_font,
                                          background=self.section_bg,
                                          anchor="nw", # Anchor text ke North-West
                                          justify="left")
                details_label.pack(fill="both", expand=True, padx=10, pady=(5 if job_title_text else 0))

                # Fungsi untuk update wraplength 
                def _update_wraplength(event, label_widget=details_label):
                    padding_adjustment = 20 # (10 padding kiri + 10 padding kanan dari details_label.pack)
                    new_wraplength = event.width - padding_adjustment
                    if new_wraplength > 0:
                        label_widget.config(wraplength=new_wraplength)
                    else:
                        # Fallback jika lebar masih sangat kecil (saat inisialisasi)
                        label_widget.config(wraplength=300) # Default kecil

                details_content_frame.bind("<Configure>", _update_wraplength)
                details_content_frame.after(10, lambda e=tk.Event(), w=details_content_frame, l=details_label: 
                                            _update_wraplength(type('Event', (), {'width': w.winfo_width()})(), l))


    def _create_education_section(self, parent_frame, section_title_text, education_entries):
        section_title_label = ttk.Label(parent_frame, text=section_title_text, font=self.heading_font,
                                        background="#e0e0e0")
        section_title_label.pack(anchor="w", pady=(15, 5), fill="x")

        education_entries_container = tk.Frame(parent_frame, bg=self.section_bg, padx=10, pady=0)
        education_entries_container.pack(fill="x", pady=(0, 15))

        if not education_entries:
            ttk.Label(education_entries_container, text="Not available.",
                      font=self.content_font, background=self.section_bg).pack(anchor="w", fill="x", padx=0, pady=10)
            return

        for edu_entry in education_entries:
            main_info_text = edu_entry.get('main_info', 'N/A')
            details_text = edu_entry.get('details', '')

            entry_item_frame = tk.Frame(education_entries_container, bg=self.section_bg)
            entry_item_frame.pack(fill="x", pady=(0, 10))

            edu_main_info_header_frame = tk.Frame(entry_item_frame, bg=self.heading_section_bg)
            edu_main_info_header_frame.pack(fill="x")
            actual_main_info_label = tk.Label(edu_main_info_header_frame, text=main_info_text,
                                              font=self.content_font_bold,
                                              bg=self.heading_section_bg, fg=self.heading_text_color,
                                              padx=10, pady=4, anchor="w", justify="left")
            actual_main_info_label.pack(fill="x")

            if details_text:
                details_content_frame = tk.Frame(entry_item_frame, bg=self.section_bg, padx=0)
                details_content_frame.pack(fill="x", expand=True)
                
                details_label = ttk.Label(details_content_frame, text=details_text,
                                          font=self.content_font,
                                          background=self.section_bg,
                                          anchor="nw",
                                          justify="left")
                details_label.pack(fill="both", expand=True, padx=10, pady=(5 if main_info_text else 0))

                def _update_wraplength(event, label_widget=details_label):
                    padding_adjustment = 20 
                    new_wraplength = event.width - padding_adjustment
                    if new_wraplength > 0:
                        label_widget.config(wraplength=new_wraplength)
                    else:
                        label_widget.config(wraplength=300)

                details_content_frame.bind("<Configure>", _update_wraplength)
                details_content_frame.after(10, lambda e=tk.Event(), w=details_content_frame, l=details_label: 
                                            _update_wraplength(type('Event', (), {'width': w.winfo_width()})(), l))
    

if __name__ == '__main__':
    try:
        from fileextract import extract_text_from_pdf 
        from kmp import KMP
    except ImportError:
        print("Gagal memuat modul penting. Aplikasi akan keluar.")
        sys.exit(1)
        
    root = tk.Tk()
    app = CVAnalyzerApp(root)
    root.mainloop()