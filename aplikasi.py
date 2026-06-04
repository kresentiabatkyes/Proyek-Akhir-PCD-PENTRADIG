import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import ctypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass


class ImageProcessingApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Aplikasi Pengolahan Citra Digital")
        self.root.geometry("1300x750")
        self.root.configure(bg="#E8ECEF")
        self.root.minsize(1200, 650)

        self.original_img = None
        self.processed_img = None
        self.display_img = None

        self.setup_ui()

    def setup_ui(self):
        # HEADER
        header = tk.Frame(self.root, bg="#2C3E50", height=55)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="PENTRADIG",
                 font=("Segoe UI", 15, "bold"), bg="#2C3E50", fg="white").pack(pady=12)

        # MAIN CONTENT
        main_content = tk.Frame(self.root, bg="#E8ECEF")
        main_content.pack(fill="both", expand=True, padx=10, pady=10)

        # SIDEBAR KIRI 
        sidebar = tk.Frame(main_content, bg="#E8ECEF", width=360)
        sidebar.pack(side="left", fill="y", padx=(0, 10))
        sidebar.pack_propagate(False)

        # Scrollable canvas
        canvas = tk.Canvas(sidebar, bg="#E8ECEF", highlightthickness=0)
        scrollbar = tk.Scrollbar(sidebar, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        control_frame = tk.Frame(canvas, bg="#E8ECEF")
        canvas_window = canvas.create_window((0, 0), window=control_frame, anchor="nw")

        def on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        control_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        def on_mousewheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # ===== TOMBOL UTAMA =====
        btn_frame = tk.Frame(control_frame, bg="#E8ECEF")
        btn_frame.pack(fill="x", pady=8, padx=5)

        btn_style = {"font": ("Segoe UI", 10), "padx": 12, "pady": 6,
                     "relief": "flat", "cursor": "hand2"}

        tk.Button(btn_frame, text="📂 Buka Gambar", command=self.open_image,
                  bg="#3498DB", fg="white", **btn_style).pack(fill="x", pady=3)
        tk.Button(btn_frame, text="💾 Simpan Hasil", command=self.save_image,
                  bg="#27AE60", fg="white", **btn_style).pack(fill="x", pady=3)
        tk.Button(btn_frame, text="🔄 Reset", command=self.reset_image,
                  bg="#E67E22", fg="white", **btn_style).pack(fill="x", pady=3)

        # ===== PROSES DASAR =====
        basic_frame = tk.LabelFrame(control_frame, text="📌 Proses Dasar",
                                     font=("Segoe UI", 10, "bold"),
                                     bg="white", fg="#2C3E50", bd=1, relief="groove")
        basic_frame.pack(fill="x", padx=5, pady=5)

        btn_row = tk.Frame(basic_frame, bg="white")
        btn_row.pack(fill="x", padx=8, pady=5)
        tk.Button(btn_row, text="⬜ Grayscale", command=self.grayscale,
                  bg="#ECF0F1", fg="#2C3E50", font=("Segoe UI", 9),
                  relief="flat", cursor="hand2", width=12).pack(side="left", padx=2)
        tk.Button(btn_row, text="⚫ Citra Biner", command=self.binary,
                  bg="#ECF0F1", fg="#2C3E50", font=("Segoe UI", 9),
                  relief="flat", cursor="hand2", width=12).pack(side="left", padx=2)

        tk.Label(basic_frame, text="Threshold:", bg="white", fg="#7F8C8D",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=8, pady=(5,0))
        self.threshold_slider = tk.Scale(basic_frame, from_=0, to=255, orient="horizontal",
                                          bg="white", fg="#2C3E50", highlightthickness=0,
                                          length=280, command=self.on_threshold_live)
        self.threshold_slider.set(127)
        self.threshold_slider.pack(pady=3, padx=8)
        self.threshold_value_label = tk.Label(basic_frame, text="Nilai: 127", bg="white", fg="#3498DB",
                                               font=("Segoe UI", 9, "bold"))
        self.threshold_value_label.pack(pady=(0, 5))

        # ===== KECERAHAN =====
        bright_frame = tk.LabelFrame(control_frame, text="☀️ Kecerahan",
                                      font=("Segoe UI", 10, "bold"),
                                      bg="white", fg="#2C3E50", bd=1, relief="groove")
        bright_frame.pack(fill="x", padx=5, pady=5)

        self.brightness_slider = tk.Scale(bright_frame, from_=-100, to=100, orient="horizontal",
                                           bg="white", fg="#2C3E50", highlightthickness=0,
                                           length=280, command=self.on_brightness_live)
        self.brightness_slider.set(0)
        self.brightness_slider.pack(pady=5, padx=8)
        self.brightness_value_label = tk.Label(bright_frame, text="Nilai: 0", bg="white", fg="#3498DB",
                                                font=("Segoe UI", 9, "bold"))
        self.brightness_value_label.pack(pady=(0, 8))

        # ===== OPERASI LOGIKA =====
        logic_frame = tk.LabelFrame(control_frame, text="🔘 Operasi Logika",
                                     font=("Segoe UI", 10, "bold"),
                                     bg="white", fg="#2C3E50", bd=1, relief="groove")
        logic_frame.pack(fill="x", padx=5, pady=5)

        self.logic_var = tk.StringVar(value="AND")
        logic_btns = tk.Frame(logic_frame, bg="white")
        logic_btns.pack(pady=8)
        ops = [("NOT", 0), ("AND", 1), ("OR", 2), ("XOR", 3)]
        for text, col in ops:
            
            tk.Radiobutton(logic_btns, text=text, variable=self.logic_var, value=text,
                           bg="white", fg="#2C3E50", selectcolor="#BDC3C7",
                           activebackground="#ECF0F1", activeforeground="#2C3E50").grid(row=0, column=col, padx=6)

        tk.Button(logic_frame, text="Terapkan", command=self.apply_logic,
                  bg="#3498DB", fg="white", font=("Segoe UI", 9),
                  relief="flat", cursor="hand2").pack(fill="x", padx=8, pady=8)

        # ===== HISTOGRAM =====
        hist_frame = tk.LabelFrame(control_frame, text="📊 Histogram",
                                    font=("Segoe UI", 10, "bold"),
                                    bg="white", fg="#2C3E50", bd=1, relief="groove")
        hist_frame.pack(fill="x", padx=5, pady=5)

        tk.Button(hist_frame, text="Tampilkan Histogram", command=self.show_histogram,
                  bg="#9B59B6", fg="white", font=("Segoe UI", 9),
                  relief="flat", cursor="hand2").pack(fill="x", padx=8, pady=8)

        # ===== KONVOLUSI =====
        conv_frame = tk.LabelFrame(control_frame, text="🎛️ Konvolusi / Filter",
                                    font=("Segoe UI", 10, "bold"),
                                    bg="white", fg="#2C3E50", bd=1, relief="groove")
        conv_frame.pack(fill="x", padx=5, pady=5)

        self.conv_var = tk.StringVar(value="Blur")
        conv_btns = tk.Frame(conv_frame, bg="white")
        conv_btns.pack(pady=8)
        filters = [("Blur", 0), ("Sharpen", 1), ("Edge Detection", 2)]
        for text, col in filters:
            tk.Radiobutton(conv_btns, text=text, variable=self.conv_var, value=text,
                           bg="white", fg="#2C3E50", selectcolor="#BDC3C7").grid(row=0, column=col, padx=8)

        tk.Button(conv_frame, text="Terapkan", command=self.apply_convolution,
                  bg="#3498DB", fg="white", font=("Segoe UI", 9),
                  relief="flat", cursor="hand2").pack(fill="x", padx=8, pady=8)

        # ===== MORFOLOGI =====
        morph_frame = tk.LabelFrame(control_frame, text="🧬 Morfologi",
                                     font=("Segoe UI", 10, "bold"),
                                     bg="white", fg="#2C3E50", bd=1, relief="groove")
        morph_frame.pack(fill="x", padx=5, pady=5)

        self.morph_var = tk.StringVar(value="Erosi")
        self.se_var = tk.StringVar(value="Rect")

        morph_type = tk.Frame(morph_frame, bg="white")
        morph_type.pack(pady=8)
        tk.Radiobutton(morph_type, text="Erosi", variable=self.morph_var, value="Erosi",
                       bg="white", fg="#2C3E50", selectcolor="#BDC3C7").pack(side="left", padx=15)
        tk.Radiobutton(morph_type, text="Dilasi", variable=self.morph_var, value="Dilasi",
                       bg="white", fg="#2C3E50", selectcolor="#BDC3C7").pack(side="left", padx=15)

        tk.Label(morph_frame, text="Elemen Struktur:", bg="white", fg="#7F8C8D",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=8, pady=(5,0))
        se_btns = tk.Frame(morph_frame, bg="white")
        se_btns.pack(pady=5)
        for i, se in enumerate(["Rect", "Ellipse", "Cross"]):
            tk.Radiobutton(se_btns, text=se, variable=self.se_var, value=se,
                           bg="white", fg="#2C3E50", selectcolor="#BDC3C7").grid(row=0, column=i, padx=15)

        tk.Button(morph_frame, text="Terapkan", command=self.apply_morphology,
                  bg="#3498DB", fg="white", font=("Segoe UI", 9),
                  relief="flat", cursor="hand2").pack(fill="x", padx=8, pady=8)

        # ===== AREA GAMBAR =====
        image_area = tk.Frame(main_content, bg="#E8ECEF")
        image_area.pack(side="right", fill="both", expand=True)

        # Kiri: Gambar Asli
        left_img_frame = tk.LabelFrame(image_area, text="📷 GAMBAR ASLI",
                                        font=("Segoe UI", 11, "bold"),
                                        bg="white", fg="#2C3E50", bd=2, relief="groove")
        left_img_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.original_label = tk.Label(left_img_frame, bg="#F8F9FA",
                                        text="Belum ada gambar\nKlik 'Buka Gambar'",
                                        font=("Segoe UI", 10), fg="#95A5A6")
        self.original_label.pack(expand=True, fill="both", padx=5, pady=5)

        # Kanan: Hasil Proses
        right_img_frame = tk.LabelFrame(image_area, text="✨ HASIL PROSES",
                                         font=("Segoe UI", 11, "bold"),
                                         bg="white", fg="#2C3E50", bd=2, relief="groove")
        right_img_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        self.result_label = tk.Label(right_img_frame, bg="#F8F9FA",
                                      text="Hasil akan muncul di sini",
                                      font=("Segoe UI", 10), fg="#95A5A6")
        self.result_label.pack(expand=True, fill="both", padx=5, pady=5)

        # Status Bar
        status_frame = tk.Frame(self.root, bg="#D5DBDB", height=28)
        status_frame.pack(fill="x", side="bottom")
        self.status_label = tk.Label(status_frame, text="✅ Siap | Geser slider untuk mengubah brightness dan threshold secara real-time",
                                      bg="#D5DBDB", fg="#2C3E50", font=("Segoe UI", 8))
        self.status_label.pack(side="left", padx=10)

    def set_status(self, msg):
        self.status_label.config(text=f"✅ {msg}")
        self.root.update_idletasks()

    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image", "*.jpg *.png *.bmp *.jpeg")])
        if path:
            self.original_img = cv2.imread(path)
            self.processed_img = self.original_img.copy()
            self.display_img = self.original_img.copy()
            self.brightness_slider.set(0)
            self.brightness_value_label.config(text="Nilai: 0")
            self.threshold_slider.set(127)
            self.threshold_value_label.config(text="Nilai: 127")
            self.display_images()
            self.set_status("Gambar dimuat")

    def save_image(self):
        if self.processed_img is None:
            messagebox.showwarning("Peringatan", "Tidak ada gambar untuk disimpan")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                              filetypes=[("PNG", "*.png"), ("JPG", "*.jpg")])
        if path:
            cv2.imwrite(path, self.processed_img)
            self.set_status("Gambar disimpan")

    def reset_image(self):
        if self.original_img is not None:
            self.processed_img = self.original_img.copy()
            self.display_img = self.original_img.copy()
            self.brightness_slider.set(0)
            self.brightness_value_label.config(text="Nilai: 0")
            self.threshold_slider.set(127)
            self.threshold_value_label.config(text="Nilai: 127")
            self.display_images()
            self.set_status("Reset ke gambar asli")

    def display_images(self):
        if self.original_img is not None:
            img = self.resize_image(self.original_img)
            self.original_label.config(image=img, text="")
            self.original_label.image = img
        else:
            self.original_label.config(text="Belum ada gambar\nKlik 'Buka Gambar'")

        if self.display_img is not None:
            img = self.resize_image(self.display_img)
            self.result_label.config(image=img, text="")
            self.result_label.image = img
        else:
            self.result_label.config(text="Hasil akan muncul di sini")

    def resize_image(self, img, max_w=480, max_h=380):
        if img is None:
            return None
        if len(img.shape) == 2:
            rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        if h > max_h or w > max_w:
            r = min(max_h/h, max_w/w)
            new = (int(w*r), int(h*r))
            rgb = cv2.resize(rgb, new)
        return ImageTk.PhotoImage(Image.fromarray(rgb))

    def on_threshold_live(self, val):
        if self.original_img is None:
            return
        thresh_val = int(float(val))
        self.threshold_value_label.config(text=f"Nilai: {thresh_val}")
        
        if len(self.original_img.shape) == 3:
            gray = cv2.cvtColor(self.original_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = self.original_img.copy()
            
        _, binary_img = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)
        
        self.processed_img = binary_img.copy()
        self.display_img = binary_img.copy()
        
        self.display_images()
        self.set_status(f"Threshold: {thresh_val}")

    def on_brightness_live(self, val):
        if self.original_img is None:
            return
        brightness_val = int(float(val))
        self.brightness_value_label.config(text=f"Nilai: {brightness_val}")
        
        self.processed_img = cv2.convertScaleAbs(self.original_img, alpha=1, beta=brightness_val)
        self.display_img = self.processed_img.copy()
        
        self.display_images()
        self.set_status(f"Kecerahan: {brightness_val}")

    def grayscale(self):
        if self.original_img is None:
            messagebox.showwarning("Peringatan", "Buka gambar terlebih dahulu")
            return
        self.brightness_slider.set(0)
        self.brightness_value_label.config(text="Nilai: 0")
        self.threshold_slider.set(127)
        self.threshold_value_label.config(text="Nilai: 127")
        if len(self.processed_img.shape) == 3:
            self.processed_img = cv2.cvtColor(self.processed_img, cv2.COLOR_BGR2GRAY)
        else:
            self.processed_img = self.processed_img.copy()
        self.display_img = self.processed_img.copy()
        self.display_images()
        self.set_status("Grayscale diterapkan")

    def binary(self):
        if self.original_img is None:
            messagebox.showwarning("Peringatan", "Buka gambar terlebih dahulu")
            return
        self.brightness_slider.set(0)
        self.brightness_value_label.config(text="Nilai: 0")
        thresh = self.threshold_slider.get()
        if len(self.processed_img.shape) == 3:
            gray = cv2.cvtColor(self.processed_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = self.processed_img.copy()
        _, self.processed_img = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)
        self.display_img = self.processed_img.copy()
        self.display_images()
        self.set_status(f"Citra biner (threshold={int(thresh)})")

    def get_binary_img(self, img):
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        return binary

    def apply_logic(self):
        if self.original_img is None:
            messagebox.showwarning("Peringatan", "Buka gambar terlebih dahulu")
            return
        self.brightness_slider.set(0)
        self.brightness_value_label.config(text="Nilai: 0")
        self.threshold_slider.set(127)
        self.threshold_value_label.config(text="Nilai: 127")
        op = self.logic_var.get()
        if len(self.processed_img.shape) == 3:
            gray = cv2.cvtColor(self.processed_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = self.processed_img.copy()
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        if op == "NOT":
            self.processed_img = cv2.bitwise_not(binary)
        elif op == "AND":
            self.processed_img = cv2.bitwise_and(binary, binary)
        elif op == "OR":
            self.processed_img = cv2.bitwise_or(binary, binary)
        elif op == "XOR":
            self.processed_img = cv2.bitwise_xor(binary, binary)
        self.display_img = self.processed_img.copy()
        self.display_images()
        self.set_status(f"Logika {op} diterapkan")

    def show_histogram(self):
        if self.original_img is None:
            messagebox.showwarning("Peringatan", "Buka gambar terlebih dahulu")
            return
        img = self.display_img if self.display_img is not None else self.original_img
        plt.figure(figsize=(9, 5), facecolor='white')
        if len(img.shape) == 2:
            hist = cv2.calcHist([img], [0], None, [256], [0, 256])
            plt.plot(hist, color='#3498DB', linewidth=2)
            plt.title("Histogram Grayscale", fontsize=12, color='#2C3E50')
        else:
            colors = ['#3498DB', '#27AE60', '#E74C3C']
            labels = ['Blue', 'Green', 'Red']
            for i, (c, lbl) in enumerate(zip(colors, labels)):
                hist = cv2.calcHist([img], [i], None, [256], [0, 256])
                plt.plot(hist, color=c, label=lbl, linewidth=2)
            plt.legend()
            plt.title("Histogram RGB", fontsize=12, color='#2C3E50')
        plt.xlabel("Intensitas Pixel", color='#2C3E50')
        plt.ylabel("Frekuensi", color='#2C3E50')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
        self.set_status("Histogram ditampilkan")

    def apply_convolution(self):
        if self.original_img is None:
            messagebox.showwarning("Peringatan", "Buka gambar terlebih dahulu")
            return
        self.brightness_slider.set(0)
        self.brightness_value_label.config(text="Nilai: 0")
        self.threshold_slider.set(127)
        self.threshold_value_label.config(text="Nilai: 127")
        f = self.conv_var.get()
        if f == "Blur":
            self.processed_img = cv2.GaussianBlur(self.processed_img, (9, 9), 0)
        elif f == "Sharpen":
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            self.processed_img = cv2.filter2D(self.processed_img, -1, kernel)
        else:
            if len(self.processed_img.shape) == 3:
                gray = cv2.cvtColor(self.processed_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = self.processed_img.copy()
            self.processed_img = cv2.Canny(gray, 100, 200)
        self.display_img = self.processed_img.copy()
        self.display_images()
        self.set_status(f"Filter {f} diterapkan")

    def apply_morphology(self):
        if self.original_img is None:
            messagebox.showwarning("Peringatan", "Buka gambar terlebih dahulu")
            return
        self.brightness_slider.set(0)
        self.brightness_value_label.config(text="Nilai: 0")
        self.threshold_slider.set(127)
        self.threshold_value_label.config(text="Nilai: 127")
        if len(self.processed_img.shape) == 3:
            gray = cv2.cvtColor(self.processed_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = self.processed_img.copy()
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        se = self.se_var.get()
        if se == "Rect":
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        elif se == "Ellipse":
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        else:
            kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (5, 5))
        if self.morph_var.get() == "Erosi":
            self.processed_img = cv2.erode(binary, kernel, 1)
        else:
            self.processed_img = cv2.dilate(binary, kernel, 1)
        self.display_img = self.processed_img.copy()
        self.display_images()
        self.set_status(f"Morfologi: {self.morph_var.get()} ({se})")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessingApp(root)
    root.mainloop()
