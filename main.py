import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
import shutil
import os
import threading
from bs4 import BeautifulSoup

class MangaDownloaderGUI:
    BASE_URL = "https://mangabuddy.com/"
    
    def __init__(self, master):
        self.master = master
        master.title("Manga Downloader")
        master.geometry("600x550")

        self.manga_name_label = tk.Label(master, text="Manga Name:")
        self.manga_name_label.pack()

        self.manga_name_entry = tk.Entry(master, width=60)
        self.manga_name_entry.pack()

        self.chapter_start_label = tk.Label(master, text="Start Chapter:")
        self.chapter_start_label.pack()

        self.chapter_start_entry = tk.Entry(master, width=10)
        self.chapter_start_entry.pack()

        self.chapter_end_label = tk.Label(master, text="End Chapter:")
        self.chapter_end_label.pack()

        self.chapter_end_entry = tk.Entry(master, width=10)
        self.chapter_end_entry.pack()

        self.path_label = tk.Label(master, text="Download Path:")
        self.path_label.pack()

        self.path_entry = tk.Entry(master, width=60)
        self.path_entry.pack()

        self.download_button = tk.Button(master, text="Start Download", command=self.start_download)
        self.download_button.pack(pady=10)

        self.stop_button = tk.Button(master, text="Stop Download", command=self.stop_download, state="disabled")
        self.stop_button.pack(pady=10)

        self.progress = ttk.Progressbar(master, orient="horizontal", length=500, mode="determinate")
        self.progress.pack(pady=10)

        self.status_text = scrolledtext.ScrolledText(master, width=70, height=15)
        self.status_text.pack(pady=10)

        self.stop_event = threading.Event()

    def start_download(self):
        self.stop_event.clear()
        self.download_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress['value'] = 0
        self.update_status("Starting download...")
        self.master.update_idletasks()
        threading.Thread(target=self.download_manga, daemon=True).start()

    def stop_download(self):
        self.stop_event.set()
        self.update_status("Download stopping...")
        self.download_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def get_number_of_images(self, chapter_url):
        try:
            response = requests.get(chapter_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            # Assuming images are in <img> tags with src attributes
            images = soup.find_all('img', src=True)
            # Adjust the image extraction based on the specific page structure
            return len(images)
        except Exception as e:
            self.update_status(f"Error retrieving number of images: {str(e)}")
            return 0

    def download_manga(self):
        manga_name = self.manga_name_entry.get().strip().replace(" ", "-").lower()
        start_chap = int(self.chapter_start_entry.get().strip())
        end_chap = int(self.chapter_end_entry.get().strip())
        working_path = self.path_entry.get().strip()
        main_folder = 'myfavouritemanga'
        
        try:
            os.makedirs(os.path.join(working_path, main_folder), exist_ok=True)
            self.update_status(f"Main folder '{main_folder}' created in '{working_path}'")
        except Exception as e:
            self.update_status(f"Error creating main folder: {str(e)}")
            self.reset_ui()
            return

        total_chapters = end_chap - start_chap + 1
        for chap in range(start_chap, end_chap + 1):
            if self.stop_event.is_set():
                break

            chap2 = '{:0>4}'.format(chap)
            path = os.path.join(working_path, main_folder, chap2)

            try:
                os.makedirs(path, exist_ok=True)
                self.update_status(f"Created folder for chapter {chap2}: {path}")
            except Exception as e:
                self.update_status(f"Error creating folder '{path}': {str(e)}")
                continue

            chapter_url = f"{self.BASE_URL}{manga_name}/chapter-{chap}"
            num_images = self.get_number_of_images(chapter_url)

            if num_images == 0:
                self.update_status(f"No images found for chapter {chap2}")
                continue

            pag = 1
            while pag <= num_images:
                if self.stop_event.is_set():
                    break

                pag2 = '{:0>3}'.format(pag)
                url = f"{self.BASE_URL}{manga_name}/chapter-{chap}/{pag2}.png"
                file_name = os.path.join(path, f"{chap2}-{pag2}.png")

                self.update_status(f"Attempting to download from URL: {url}")

                try:
                    res = requests.get(url, stream=True)
                    if res.status_code == 200:
                        with open(file_name, 'wb') as f:
                            shutil.copyfileobj(res.raw, f)
                        self.update_status(f"Image successfully downloaded: {file_name}")
                        pag += 1
                    else:
                        self.update_status(f"Image not found at {url}")
                        pag += 1
                except Exception as e:
                    self.update_status(f"Error downloading image {url}: {str(e)}")
                    pag += 1

            self.update_status(f"Chapter {chap2} downloaded successfully")
            self.progress['value'] = (chap - start_chap + 1) / total_chapters * 100
            self.master.update_idletasks()

        self.update_status("All chapters downloaded successfully")
        self.reset_ui()

    def update_status(self, message):
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        print(message)

    def reset_ui(self):
        self.progress['value'] = 0
        self.download_button.config(state="normal")
        self.stop_button.config(state="disabled")

root = tk.Tk()
app = MangaDownloaderGUI(root)
root.mainloop()
