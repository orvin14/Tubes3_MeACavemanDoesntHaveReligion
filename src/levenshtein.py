from concurrent.futures import ThreadPoolExecutor
import math

def levenshteinDistance(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    
    dp = [[0]*(n+1) for _ in range(m+1)]

    # Inisialisasi baris dan kolom pertama
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # Isi sisa matriks 
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            
            # Ambil nilai minimum dari operasi (penghapusan, penyisipan, substitusi)
            dp[i][j] = min(dp[i - 1][j] + 1,        # Penghapusan
                           dp[i][j - 1] + 1,        # Penyisipan
                           dp[i - 1][j - 1] + cost) # Substitusi

    # Hasil akhir ada di pojok kanan bawah matriks
    return dp[m][n]

def levenshteinSearch(text: str, pattern: str, threshold: int = 1) -> int:
    words = text.split()
    count = 0
    for word in words:
        if levenshteinDistance(word, pattern) <= threshold:
            count += 1
            
    return count

def levenshteinSearchWithMatchedWords(text: str, pattern: str, threshold: int = 1) -> tuple[int, list[str]]:
    words = text.split()
    count = 0
    matched_words = []
    for word in words:
        if levenshteinDistance(word, pattern) <= threshold:
            count += 1
            matched_words.append(word) # Tambahkan kata yang cocok
    return count, matched_words

# def _process_chunk(chunk: list[str], pattern: str, threshold: int) -> int:
#     local_count = 0
#     for word in chunk:
#         if levenshtein_distance(word, pattern) <= threshold:
#             local_count += 1
#     return local_count

# def levenshtein_search_multithreaded(text: str, pattern: str, threshold: int = 2) -> int:

#     words = text.split()
#     total_words = len(words)

#     if total_words == 0:
#         return 0

#     num_threads = max(1, total_words // 300)
#     chunk_size = math.ceil(total_words / num_threads)

#     chunks = [words[i:i + chunk_size] for i in range(0, total_words, chunk_size)]

#     total_count = 0
#     with ThreadPoolExecutor(max_workers=num_threads) as executor:
#         futures = [executor.submit(_process_chunk, chunk, pattern, threshold) for chunk in chunks]

#         for future in futures:
#             total_count += future.result() # future.result() akan menunggu thread selesai

#     return total_count