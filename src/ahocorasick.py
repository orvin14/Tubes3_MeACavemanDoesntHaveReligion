class Node:
    def __init__(self):
        self.children = {}  # Transisi berdasarkan karakter: char -> Node
        self.failure_link = None  # Tautan kegagalan: Node
        self.output = []  # Daftar kata kunci (string) yang berakhir di node ini

class AhoCorasick:
    def __init__(self, keywords):
        if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
            raise ValueError("Keywords harus berupa daftar string")
        if not keywords: # Menangani kasus daftar kata kunci kosong
            pass


        self.root = Node()
        # Simpan daftar kata kunci asli untuk digunakan saat menginisialisasi hasil pencarian.
        self.keywords = list(set(keywords)) # Hilangkan duplikat jika ada
        if not self.keywords and keywords: # Jika setelah set jadi kosong padahal input ada (misal `["", ""]`)
             # Jika hanya string kosong yang diberikan, perlakukan sebagai tidak ada keyword valid
             self.keywords = []


        if self.keywords: # Hanya bangun trie jika ada keywords valid
            self._build_trie()
            self._build_failure_links()

    def _build_trie(self):
        """Membangun Trie (pohon kata kunci) dari daftar kata kunci."""
        for keyword in self.keywords:
            if not keyword: continue # Abaikan string kosong sebagai keyword
            node = self.root
            for char in keyword:
                node = node.children.setdefault(char, Node())
            # Tambahkan kata kunci ke output node di mana kata kunci tersebut berakhir
            node.output.append(keyword)

    def _build_failure_links(self):
        # Antrian untuk BFS, dimulai dengan anak-anak dari root
        queue = []
        for char, child_node in self.root.children.items():
            # Tautan kegagalan untuk child root selalu menunjuk ke root
            child_node.failure_link = self.root
            queue.append(child_node)

        head = 0
        while head < len(queue):
            current_node = queue[head]
            head += 1

            for char, next_node in current_node.children.items():
                queue.append(next_node)
                # Tentukan tautan kegagalan untuk next_node
                failure_candidate = current_node.failure_link
                # Selama failure_candidate ada dan tidak ada transisi untuk 'char' darinya ikuti tautan kegagalan ke atas.
                while failure_candidate is not None and char not in failure_candidate.children:
                    failure_candidate = failure_candidate.failure_link
                
                # Jika kita menemukan state kegagalan yang valid dengan transisi 'char'
                if failure_candidate:
                    next_node.failure_link = failure_candidate.children[char]
                else:
                    # Jika tidak ada (mencapai root dan root tidak punya transisi 'char'),
                    next_node.failure_link = self.root
                
                if next_node.failure_link:
                    next_node.output.extend(next_node.failure_link.output)

    def search(self, text):
        if not self.keywords: # Jika tidak ada keywords yang di-set saat init
            return {}

        # Inisialisasi dictionary untuk menyimpan hitungan setiap kata kunci
        keyword_counts = {keyword: 0 for keyword in self.keywords}
        
        current_node = self.root

        for char_index, char in enumerate(text):
            # Ikuti transisi karakter. Jika tidak ada, ikuti tautan kegagalan
            while current_node is not None and char not in current_node.children:
                current_node = current_node.failure_link
            
            if current_node is None:
                current_node = self.root
                continue # Lanjutkan ke karakter berikutnya dalam teks

            # Pindah ke state berikutnya berdasarkan karakter saat ini
            current_node = current_node.children[char]

            # Jika state saat ini memiliki output, berarti satu atau lebih kata kunci ditemukan
            if current_node.output:
                for keyword_found in current_node.output:
                    if keyword_found in keyword_counts:
                        keyword_counts[keyword_found] += 1
        
        return keyword_counts