def hitungLPS(pola):
    m = len(pola)
    lps = [0] * m
    panjang = 0
    i = 1

    while i < m:
        if pola[i] == pola[panjang]:
            panjang += 1
            lps[i] = panjang
            i += 1
        else:
            if panjang != 0:
                panjang = lps[panjang - 1]
            else:
                lps[i] = 0
                i += 1

    return lps
def KMP(teks, pola):
    n = len(teks)
    m = len(pola)
    count = 0

    if m == 0:
        return 0 # Pola kosong tidak dianggap muncul
    if m > n:
        return 0
    lps = hitungLPS(pola)
    i = 0  # Indeks untuk teks
    j = 0  # Indeks untuk pola

    while i < n:
        if pola[j] == teks[i]:
            i += 1
            j += 1

        # Jika seluruh pola telah cocok
        if j == m:
            count += 1
            j = lps[j - 1]

        # Ketidakcocokan setelah beberapa kecocokan
        elif i < n and pola[j] != teks[i]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1

    return count
    