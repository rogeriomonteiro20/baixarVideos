# 🎬 YouTube Downloader (Desktop GUI)

Aplicação desktop em Python com interface gráfica moderna (Dark Mode) construída com **Tkinter** e **yt-dlp** para baixar vídeos (**MP4**) e áudios (**MP3**) do YouTube com seleção de qualidade e barra de progresso em tempo real.

---

## ✨ Funcionalidades

- **Interface Gráfica Escura (Dark Mode):** Visual limpo e intuitivo estilizado com `ttk` (tema `clam`).
- **Download de Vídeos (MP4):** Suporte para resoluções de `360p`, `480p`, `720p`, `1080p (Full HD)` ou a `Melhor Disponível`.
- **Extração de Áudio (MP3):** Conversão direta para MP3 nas qualidades `128 kbps`, `192 kbps` e `320 kbps`.
- **FFmpeg Automático:** Integração com `imageio-ffmpeg` para unir faixas de vídeo/áudio em alta definição e converter MP3 sem precisar configurar variáveis de ambiente (PATH) manualmente no sistema.
- **Progresso em Tempo Real:** Barra de progresso personalizada que exibe porcentagem concluída, velocidade de download (MB/s) e tempo restante estimado (ETA).
- **Execução Assíncrona (`Threading`):** O download roda em segundo plano, mantendo a janela responsiva sem travamentos.
- **Escolha de Diretório:** Cria automaticamente uma pasta `downloads/`, mas permite selecionar qualquer outra pasta no computador.

---

## 🛠️ Pré-requisitos

Certifique-se de ter o **Python 3.8+** instalado no seu sistema.

As bibliotecas externas utilizadas no projeto são:
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) — Motor de download de mídia.
- [`imageio-ffmpeg`](https://github.com/imageio/imageio-ffmpeg) — Binário embutido do FFmpeg para mesclagem de vídeo/áudio em 1080p+ e conversão para MP3.

*(Módulos como `tkinter`, `threading` e `os` já vêm nativamente na instalação padrão do Python).*

---

## 🚀 Instalação e Configuração

1. **Clone o repositório ou baixe os arquivos do projeto:**
   ```bash
   git clone [https://github.com/seu-usuario/BaixarVideos.git](https://github.com/seu-usuario/BaixarVideos.git)
   cd BaixarVideos
