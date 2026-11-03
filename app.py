import os
import uuid
import glob
import threading
from flask import Flask, render_template_string, request, jsonify, send_file, after_this_request
import yt_dlp

# Localiza o FFmpeg automaticamente
try:
    import imageio_ffmpeg
    CAMINHO_FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    CAMINHO_FFMPEG = None

app = Flask(__name__)

# Pasta temporária no servidor para processar os downloads
PASTA_TEMP = os.path.join(os.getcwd(), "temp_downloads")
os.makedirs(PASTA_TEMP, exist_ok=True)

# Dicionário em memória para guardar o progresso de cada download
TAREFAS = {}

# Interface Web (HTML + CSS + JS) mantendo a identidade visual escura
HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Downloader Web</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body {
            background-color: #11111b;
            color: #cdd6f4;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .card {
            background-color: #1e1e2e;
            width: 100%;
            max-width: 520px;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
        }
        h1 { text-align: center; font-size: 24px; margin-bottom: 24px; color: #cdd6f4; }
        label { display: block; font-size: 14px; font-weight: 600; color: #bac2de; margin-bottom: 8px; }
        input[type="text"], select {
            width: 100%;
            padding: 12px 14px;
            background-color: #313244;
            border: 1px solid #45475a;
            border-radius: 8px;
            color: #cdd6f4;
            font-size: 14px;
            outline: none;
            transition: border 0.2s;
        }
        input[type="text"]:focus, select:focus { border-color: #89b4fa; }
        .row { display: flex; gap: 20px; margin-top: 18px; }
        .col { flex: 1; }
        .radio-group { display: flex; flex-direction: column; gap: 8px; margin-top: 4px; }
        .radio-label {
            display: flex; align-items: center; gap: 8px;
            font-weight: normal; color: #cdd6f4; cursor: pointer;
        }
        input[type="radio"] { accent-color: #a6e3a1; transform: scale(1.15); }
        .progress-wrapper { margin-top: 25px; }
        .progress-bg {
            width: 100%;
            height: 22px;
            background-color: #313244;
            border-radius: 11px;
            overflow: hidden;
        }
        .progress-bar {
            width: 0%;
            height: 100%;
            background-color: #a6e3a1;
            transition: width 0.25s ease;
        }
        .status-text {
            text-align: center;
            font-size: 13px;
            color: #a6adc8;
            margin-top: 10px;
            min-height: 20px;
        }
        button {
            width: 100%;
            margin-top: 22px;
            padding: 14px;
            background-color: #89b4fa;
            color: #11111b;
            font-size: 15px;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s, transform 0.1s;
        }
        button:hover:not(:disabled) { background-color: #b4befe; }
        button:disabled { background-color: #585b70; color: #a6adc8; cursor: not-allowed; }
    </style>
</head>
<body>
    <div class="card">
        <h1>YouTube Downloader</h1>

        <div>
            <label for="url">Link do Vídeo:</label>
            <input type="text" id="url" placeholder="https://www.youtube.com/watch?v=..." autocomplete="off">
        </div>

        <div class="row">
            <div class="col">
                <label>Formato:</label>
                <div class="radio-group">
                    <label class="radio-label">
                        <input type="radio" name="tipo" value="mp4" checked onchange="atualizarQualidade()"> Vídeo (MP4)
                    </label>
                    <label class="radio-label">
                        <input type="radio" name="tipo" value="mp3" onchange="atualizarQualidade()"> Áudio (MP3)
                    </label>
                </div>
            </div>

            <div class="col">
                <label for="qualidade">Qualidade:</label>
                <select id="qualidade"></select>
            </div>
        </div>

        <div class="progress-wrapper">
            <div class="progress-bg">
                <div class="progress-bar" id="barra"></div>
            </div>
            <div class="status-text" id="status">Aguardando link...</div>
        </div>

        <button id="btnBaixar" onclick="iniciarDownload()">BAIXAR AGORA</button>
    </div>

    <script>
        const opcoesVideo = ["Melhor Disponível", "1080p", "720p", "480p", "360p"];
        const opcoesAudio = ["320 kbps", "192 kbps", "128 kbps"];

        function atualizarQualidade() {
            const tipo = document.querySelector('input[name="tipo"]:checked').value;
            const select = document.getElementById("qualidade");
            select.innerHTML = "";
            const lista = tipo === "mp4" ? opcoesVideo : opcoesAudio;

            lista.forEach((op, idx) => {
                const option = document.createElement("option");
                option.value = op;
                option.textContent = op;
                if (idx === 1) option.selected = true; // Padrão: 1080p ou 192 kbps
                select.appendChild(option);
            });
        }

        async function iniciarDownload() {
            const url = document.getElementById("url").value.trim();
            const tipo = document.querySelector('input[name="tipo"]:checked').value;
            const qualidade = document.getElementById("qualidade").value;
            const btn = document.getElementById("btnBaixar");
            const barra = document.getElementById("barra");
            const status = document.getElementById("status");

            if (!url) {
                alert("Cole um link válido do YouTube.");
                return;
            }

            btn.disabled = true;
            btn.textContent = "PROCESSANDO...";
            barra.style.width = "0%";
            status.textContent = "Iniciando download no servidor...";

            try {
                const resp = await fetch("/iniciar", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ url, tipo, qualidade })
                });
                const dados = await resp.json();

                if (dados.erro) {
                    throw new Error(dados.erro);
                }

                acompanharProgresso(dados.task_id);
            } catch (err) {
                status.textContent = "Erro: " + err.message;
                btn.disabled = false;
                btn.textContent = "BAIXAR AGORA";
            }
        }

        function acompanharProgresso(taskId) {
            const barra = document.getElementById("barra");
            const status = document.getElementById("status");
            const btn = document.getElementById("btnBaixar");

            const intervalo = setInterval(async () => {
                try {
                    const resp = await fetch(`/progresso/${taskId}`);
                    const info = await resp.json();

                    barra.style.width = `${info.percent || 0}%`;
                    status.textContent = info.texto || "Processando...";

                    if (info.estado === "concluido") {
                        clearInterval(intervalo);
                        status.textContent = "Pronto! O download começará no seu navegador.";
                        btn.disabled = false;
                        btn.textContent = "BAIXAR AGORA";
                        // Dispara o download do arquivo pelo navegador
                        window.location.href = `/baixar_arquivo/${taskId}`;
                    } else if (info.estado === "erro") {
                        clearInterval(intervalo);
                        barra.style.width = "0%";
                        status.textContent = "Falha: " + info.texto;
                        btn.disabled = false;
                        btn.textContent = "BAIXAR AGORA";
                    }
                } catch (e) {
                    clearInterval(intervalo);
                    status.textContent = "Erro de conexão com o servidor.";
                    btn.disabled = false;
                    btn.textContent = "BAIXAR AGORA";
                }
            }, 800);
        }

        atualizarQualidade();
    </script>
</body>
</html>
"""


def processar_download_background(task_id, url, tipo, qualidade):
    pasta_tarefa = os.path.join(PASTA_TEMP, task_id)
    os.makedirs(pasta_tarefa, exist_ok=True)

    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            baixado = d.get("downloaded_bytes", 0)
            pct = (baixado / total) * 100 if total else 0

            vel = d.get("speed")
            vel_str = f"{vel / (1024 * 1024):.2f} MB/s" if vel else "Calculando..."
            eta = d.get("eta")
            eta_str = f"{eta}s" if eta is not None else "--"

            TAREFAS[task_id].update({
                "percent": round(pct, 1),
                "texto": f"Baixando: {pct:.1f}%  •  Vel: {vel_str}  •  Restante: {eta_str}"
            })
        elif d["status"] == "finished":
            TAREFAS[task_id].update({
                "percent": 100,
                "texto": "Convertendo/Unindo arquivo com FFmpeg..."
            })

    ydl_opts = {
        "outtmpl": os.path.join(pasta_tarefa, "%(title)s.%(ext)s"),
        "noplaylist": True,
        "progress_hooks": [hook],
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
            formato = f"bestvideo[height<={alt}][ext=mp4]+bestaudio[ext=m4a]/best[height<={alt}][ext=mp4]/best[height<={alt}]"
        else:
            formato = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

        ydl_opts.update({
            "format": formato,
            "merge_output_format": "mp4",
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        arquivos = glob.glob(os.path.join(pasta_tarefa, "*"))
        if not arquivos:
            raise Exception("Arquivo final não encontrado.")

        TAREFAS[task_id].update({
            "estado": "concluido",
            "percent": 100,
            "arquivo": arquivos[0]
        })
    except Exception as e:
        TAREFAS[task_id].update({
            "estado": "erro",
            "texto": str(e)
        })


@app.route("/")
def index():
    return render_template_string(HTML_PAGE)


@app.route("/iniciar", methods=["POST"])
def iniciar():
    dados = request.get_json()
    url = dados.get("url", "").strip()
    tipo = dados.get("tipo", "mp4")
    qualidade = dados.get("qualidade", "1080p")

    if not url:
        return jsonify({"erro": "URL inválida."}), 400

    task_id = str(uuid.uuid4())
    TAREFAS[task_id] = {"estado": "baixando", "percent": 0, "texto": "Obtendo informações do vídeo..."}

    thread = threading.Thread(target=processar_download_background, args=(task_id, url, tipo, qualidade), daemon=True)
    thread.start()

    return jsonify({"task_id": task_id})


@app.route("/progresso/<task_id>")
def progresso(task_id):
    tarefa = TAREFAS.get(task_id)
    if not tarefa:
        return jsonify({"estado": "erro", "texto": "Tarefa não encontrada."}), 404
    return jsonify(tarefa)


@app.route("/baixar_arquivo/<task_id>")
def baixar_arquivo(task_id):
    tarefa = TAREFAS.get(task_id)
    if not tarefa or "arquivo" not in tarefa:
        return "Arquivo não encontrado ou expirado.", 404

    caminho_arquivo = tarefa["arquivo"]
    pasta_tarefa = os.path.dirname(caminho_arquivo)

    @after_this_request
    def limpar_temporarios(response):
        # Dica: em produção, use uma rotina periódica para apagar arquivos antigos
        return response

    return send_file(caminho_arquivo, as_attachment=True)


if __name__ == "__main__":
    # Roda localmente na porta 5000
    app.run(host="0.0.0.0", port=5000, debug=True)