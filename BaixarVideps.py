import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yt_dlp

# Localiza o executável do FFmpeg instalado pelo imageio-ffmpeg
try:
    import imageio_ffmpeg
    CAMINHO_FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    CAMINHO_FFMPEG = None


class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("520x430")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        self.pasta_destino = os.path.join(os.getcwd(), "downloads")
        os.makedirs(self.pasta_destino, exist_ok=True)

        self.configurar_estilos()
        self.criar_widgets()

    def configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor="#313244",
            background="#a6e3a1",
            bordercolor="#1e1e2e",
            lightcolor="#a6e3a1",
            darkcolor="#a6e3a1",
            thickness=22
        )

        style.configure(
            "TCombobox",
            fieldbackground="#313244",
            background="#45475a",
            foreground="#cdd6f4",
            arrowcolor="#cdd6f4"
        )

    def criar_widgets(self):
        tk.Label(
            self.root, text="YouTube Downloader", font=("Segoe UI", 16, "bold"),
            bg="#1e1e2e", fg="#cdd6f4"
        ).pack(pady=(15, 10))

        frame_url = tk.Frame(self.root, bg="#1e1e2e")
        frame_url.pack(fill="x", padx=25, pady=5)

        tk.Label(
            frame_url, text="Link do Vídeo:", font=("Segoe UI", 10, "bold"),
            bg="#1e1e2e", fg="#bac2de"
        ).pack(anchor="w")

        self.url_entry = tk.Entry(
            frame_url, font=("Segoe UI", 10), bg="#313244", fg="#cdd6f4",
            insertbackground="#cdd6f4", relief="flat", bd=6
        )
        self.url_entry.pack(fill="x", pady=5)

        frame_opcoes = tk.Frame(self.root, bg="#1e1e2e")
        frame_opcoes.pack(fill="x", padx=25, pady=10)

        frame_formato = tk.Frame(frame_opcoes, bg="#1e1e2e")
        frame_formato.pack(side="left", expand=True, fill="x")

        tk.Label(
            frame_formato, text="Formato:", font=("Segoe UI", 10, "bold"),
            bg="#1e1e2e", fg="#bac2de"
        ).pack(anchor="w")

        self.tipo_var = tk.StringVar(value="mp4")
        tk.Radiobutton(
            frame_formato, text="Vídeo (MP4)", variable=self.tipo_var, value="mp4",
            command=self.atualizar_opcoes_qualidade, bg="#1e1e2e", fg="#cdd6f4",
            selectcolor="#313244", activebackground="#1e1e2e", activeforeground="#a6e3a1",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=2)

        tk.Radiobutton(
            frame_formato, text="Áudio (MP3)", variable=self.tipo_var, value="mp3",
            command=self.atualizar_opcoes_qualidade, bg="#1e1e2e", fg="#cdd6f4",
            selectcolor="#313244", activebackground="#1e1e2e", activeforeground="#a6e3a1",
            font=("Segoe UI", 10)
        ).pack(anchor="w")

        frame_qualidade = tk.Frame(frame_opcoes, bg="#1e1e2e")
        frame_qualidade.pack(side="right", expand=True, fill="x")

        tk.Label(
            frame_qualidade, text="Qualidade:", font=("Segoe UI", 10, "bold"),
            bg="#1e1e2e", fg="#bac2de"
        ).pack(anchor="w")

        self.qualidade_combo = ttk.Combobox(
            frame_qualidade, state="readonly", font=("Segoe UI", 10)
        )
        self.qualidade_combo.pack(fill="x", pady=8)
        self.atualizar_opcoes_qualidade()

        frame_pasta = tk.Frame(self.root, bg="#1e1e2e")
        frame_pasta.pack(fill="x", padx=25, pady=5)

        self.lbl_pasta = tk.Label(
            frame_pasta, text=f"Salvar em: {self.pasta_destino}",
            font=("Segoe UI", 8), bg="#1e1e2e", fg="#a6adc8", anchor="w"
        )
        self.lbl_pasta.pack(side="left", fill="x", expand=True)

        tk.Button(
            frame_pasta, text="Alterar Pasta", command=self.escolher_pasta,
            bg="#45475a", fg="#cdd6f4", relief="flat", font=("Segoe UI", 8), padx=8
        ).pack(side="right")

        frame_progresso = tk.Frame(self.root, bg="#1e1e2e")
        frame_progresso.pack(fill="x", padx=25, pady=(15, 5))

        self.progress_bar = ttk.Progressbar(
            frame_progresso, style="Custom.Horizontal.TProgressbar",
            orient="horizontal", length=100, mode="determinate"
        )
        self.progress_bar.pack(fill="x")

        self.status_label = tk.Label(
            self.root, text="Aguardando link...", font=("Segoe UI", 9),
            bg="#1e1e2e", fg="#a6adc8"
        )
        self.status_label.pack(pady=4)

        self.btn_baixar = tk.Button(
            self.root, text="BAIXAR AGORA", font=("Segoe UI", 11, "bold"),
            bg="#89b4fa", fg="#11111b", activebackground="#b4befe",
            relief="flat", cursor="hand2", command=self.iniciar_thread_download
        )
        self.btn_baixar.pack(pady=12, ipadx=20, ipady=6)

    def atualizar_opcoes_qualidade(self):
        if self.tipo_var.get() == "mp4":
            opcoes = ["Melhor Disponível", "1080p", "720p", "480p", "360p"]
            self.qualidade_combo["values"] = opcoes
            self.qualidade_combo.current(1)
        else:
            opcoes = ["320 kbps", "192 kbps", "128 kbps"]
            self.qualidade_combo["values"] = opcoes
            self.qualidade_combo.current(1)

    def escolher_pasta(self):
        nova_pasta = filedialog.askdirectory(initialdir=self.pasta_destino)
        if nova_pasta:
            self.pasta_destino = nova_pasta
            self.lbl_pasta.config(text=f"Salvar em: {self.pasta_destino}")

    def hook_progresso(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            baixado = d.get("downloaded_bytes", 0)
            porcentagem = (baixado / total) * 100 if total else 0

            velocidade_bytes = d.get("speed")
            velocidade_str = f"{velocidade_bytes / (1024 * 1024):.2f} MB/s" if velocidade_bytes else "Calculando..."

            eta = d.get("eta")
            eta_str = f"{eta}s" if eta is not None else "--"

            texto_status = f"Baixando: {porcentagem:.1f}%  •  Vel: {velocidade_str}  •  Restante: {eta_str}"
            self.root.after(0, self.atualizar_ui_progresso, porcentagem, texto_status)

        elif d["status"] == "finished":
            self.root.after(
                0, self.atualizar_ui_progresso, 100,
                "Download concluído! Unindo arquivo com FFmpeg..."
            )

    def atualizar_ui_progresso(self, porcentagem, texto):
        self.progress_bar["value"] = porcentagem
        self.status_label.config(text=texto)

    def iniciar_thread_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Campo Vazio", "Cole um link válido do YouTube.")
            return

        self.btn_baixar.config(state="disabled", bg="#585b70", text="BAIXANDO...")
        self.progress_bar["value"] = 0
        self.status_label.config(text="Obtendo informações do vídeo...")

        thread = threading.Thread(target=self.executar_download, args=(url,), daemon=True)
        thread.start()

    def executar_download(self, url):
        tipo = self.tipo_var.get()
        qualidade = self.qualidade_combo.get()

        ydl_opts = {
            "outtmpl": os.path.join(self.pasta_destino, "%(title)s.%(ext)s"),
            "noplaylist": True,
            "progress_hooks": [self.hook_progresso],
            "quiet": True,
            "no_warnings": True,
            "color": "no_color",
        }

        if CAMINHO_FFMPEG:
            ydl_opts["ffmpeg_location"] = CAMINHO_FFMPEG

        if tipo == "mp3":
            bitrate = qualidade.split()[0]
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": bitrate,
                }],
            })
        else:
            mapa_res = {"1080p": "1080", "720p": "720", "480p": "480", "360p": "360"}
            if qualidade in mapa_res:
                alt = mapa_res[qualidade]
                if CAMINHO_FFMPEG:
                    formato = f"bestvideo[height<={alt}][ext=mp4]+bestaudio[ext=m4a]/best[height<={alt}][ext=mp4]/best[height<={alt}]"
                else:
                    formato = f"best[height<={alt}][ext=mp4]/best[ext=mp4]/best"
            else:
                formato = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" if CAMINHO_FFMPEG else "best[ext=mp4]/best"

            ydl_opts.update({
                "format": formato,
                "merge_output_format": "mp4",
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.root.after(0, self.finalizar_sucesso)
        except Exception as erro:
            self.root.after(0, self.finalizar_erro, str(erro))

    def finalizar_sucesso(self):
        self.status_label.config(text="Pronto! Arquivo salvo com sucesso.")
        self.btn_baixar.config(state="normal", bg="#89b4fa", text="BAIXAR AGORA")
        messagebox.showinfo("Concluído", f"Download finalizado!\nSalvo em:\n{self.pasta_destino}")

    def finalizar_erro(self, mensagem_erro):
        self.progress_bar["value"] = 0
        self.status_label.config(text="Erro ao realizar o download.")
        self.btn_baixar.config(state="normal", bg="#89b4fa", text="BAIXAR AGORA")
        messagebox.showerror("Erro no Download", f"Ocorreu uma falha:\n{mensagem_erro}")


if __name__ == "__main__":
    janela = tk.Tk()
    app = YouTubeDownloaderApp(janela)
    janela.mainloop()