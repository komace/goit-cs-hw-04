import os
import time
import threading
from multiprocessing import Process, Queue, cpu_count

# Функція для пошуку ключових слів у вказаному списку файлів
def search_keywords(file_paths, keywords):
    result = {kw: [] for kw in keywords}
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for kw in keywords:
                    if kw in content:
                        result[kw].append(file_path)
        except Exception as e:
            print(f"[Error] Cannot read file {file_path}: {e}")
    return result

# ---------- THREADING ----------
def threaded_search(file_paths, keywords):
    num_threads = min(8, len(file_paths)) # Не більше 8 потоків або менше, якщо файлів менше
    results = {kw: [] for kw in keywords}
    lock = threading.Lock() # Замок для синхронізації доступу до результатів
    threads = []

# Розбиваємо список файлів на приблизно рівні частини для кожного потоку
    chunks = [file_paths[i::num_threads] for i in range(num_threads)]

# Функція, яка виконується в кожному потоці
    def worker(chunk):
        local_result = search_keywords(chunk, keywords)

        # Додаємо знайдені результати до загального словника (з блокуванням)
        with lock:
            for kw, paths in local_result.items():
                results[kw].extend(paths)


# Створюємо та запускаємо потоки
    for chunk in chunks:
        t = threading.Thread(target=worker, args=(chunk,))
        threads.append(t)
        t.start()

# Чекаємо завершення всіх потоків
    for t in threads:
        t.join()

    return results

# ---------- MULTIPROCESSING ----------

# Окрема функція, яка запускається у процесі
def process_worker(chunk, keywords, queue):
    local_result = search_keywords(chunk, keywords)
    queue.put(local_result)


# Основна функція пошуку за допомогою multiprocessing
def multiprocessing_search(file_paths, keywords):
    num_processes = min(cpu_count(), len(file_paths)) # Використовуємо доступну кількість ядер або менше
    queue = Queue() # Черга для збору результатів
    processes = []

# Розбиваємо список файлів на частини
    chunks = [file_paths[i::num_processes] for i in range(num_processes)]

# Створюємо та запускаємо процеси
    for chunk in chunks:
        p = Process(target=process_worker, args=(chunk, keywords, queue))
        processes.append(p)
        p.start()

# Чекаємо завершення процесів
    for p in processes:
        p.join()

# Збираємо результати з черги
    final_result = {kw: [] for kw in keywords}
    while not queue.empty():
        partial = queue.get()
        for kw, paths in partial.items():
            final_result[kw].extend(paths)

    return final_result

# ---------- MAIN ----------
def main():
    keywords = ['Login', 'Password', 'Date']
    directory = '.'  # Директорія з файлами
    
    # Отримуємо список усіх .txt файлів у вказаній директорії
    file_paths = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f)) and f.endswith('.txt')
    ]


# Запуск пошуку за допомогою потоків
    print("==> Threading Search Started...")
    start_time = time.time()
    thread_result = threaded_search(file_paths, keywords)
    print(f"✅ Threading Completed in {time.time() - start_time:.2f} seconds\n")

# Запуск пошуку за допомогою процесів
    print("==> Multiprocessing Search Started...")
    start_time = time.time()
    process_result = multiprocessing_search(file_paths, keywords)
    print(f"✅ Multiprocessing Completed in {time.time() - start_time:.2f} seconds\n")

# Виведення результатів пошуку (threading)
    print("=== Results (Threading) ===")
    for kw, files in thread_result.items():
        print(f"'{kw}' found in {len(files)} file(s): {files}")

# Виведення результатів пошуку (multiprocessing)
    print("\n=== Results (Multiprocessing) ===")
    for kw, files in process_result.items():
        print(f"'{kw}' found in {len(files)} file(s): {files}")


# Запуск основної функції
if __name__ == '__main__':
    main()