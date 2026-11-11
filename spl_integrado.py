
import cv2
import serial
import time
import threading

from flask import Flask, Response, jsonify, send_file

# ==========================================
# SPL PROJECT - SISTEMA INTEGRADO WEB
# ==========================================

# CAMERA ESP32
URL_CAMERA = "http://192.168.0.49:81/stream"

# ARDUINO NANO
PORTA_ARDUINO = "COM5"
BAUDRATE = 9600

# DETECCAO DE LUZ
LIMIAR_LUZ = 220
AREA_MINIMA = 20
TOLERANCIA = 12

# SERVO
ANGULO_ATUAL = 90
VELOCIDADE_SERVO = 3
ANGULO_INVERTIDO = False

# VIDEO DO SITE
LARGURA_VIDEO = 320
ALTURA_VIDEO = 240

# ==========================================
# FLASK
# ==========================================

app = Flask(__name__)

# Guarda o ultimo video processado
ultimo_frame = None

# Evita conflitos entre as threads
trava = threading.Lock()

# Dados enviados ao dashboard
dados_sistema = {
    "status": "INICIANDO",
    "x": 0,
    "y": 0,
    "erroX": 0,
    "angulo": 90,
    "led": "VERMELHO",
    "detectado": False
}

# ==========================================
# ROTAS DO SITE
# ==========================================

@app.route("/")
def pagina_principal():
    return send_file("index.html")


@app.route("/style.css")
def arquivo_css():
    return send_file("style.css")


@app.route("/script.js")
def arquivo_javascript():
    return send_file("script.js")


@app.route("/api/status")
def api_status():
    with trava:
        return jsonify(dados_sistema.copy())


@app.route("/video_feed")
def video_feed():

    def gerar_video():

        while True:

            with trava:
                frame = ultimo_frame

            if frame is not None:

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + frame
                    + b"\r\n"
                )

            time.sleep(0.03)

    return Response(
        gerar_video(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ==========================================
# CONEXAO COM ARDUINO
# ==========================================

print("Conectando ao Arduino Nano...")

arduino = serial.Serial(
    PORTA_ARDUINO,
    BAUDRATE,
    timeout=0.1
)

# O Arduino pode reiniciar ao abrir a serial
time.sleep(2)

print("Arduino conectado!")

estado_leds = {}


def enviar_comando(comando):

    arduino.write(
        (comando + "\n").encode("utf-8")
    )

    print("Enviado:", comando)


def controlar_led(nome, ligado):

    global estado_leds

    if estado_leds.get(nome) != ligado:

        estado = "ON" if ligado else "OFF"

        enviar_comando(
            f"LED:{nome}:{estado}"
        )

        estado_leds[nome] = ligado


def controlar_servo(angulo):

    global ANGULO_ATUAL

    angulo = max(
        0,
        min(180, int(angulo))
    )

    if angulo != ANGULO_ATUAL:

        enviar_comando(
            f"SERVO:{angulo}"
        )

        ANGULO_ATUAL = angulo


# ==========================================
# CONTROLE DOS LEDS
# ==========================================

def atualizar_leds(vermelho, amarelo, verde):

    controlar_led("VERMELHO", vermelho)
    controlar_led("AMARELO", amarelo)
    controlar_led("VERDE", verde)


# ==========================================
# ATUALIZAR DADOS DO DASHBOARD
# ==========================================

def atualizar_dados(
    status,
    x=0,
    y=0,
    erro_x=0,
    detectado=False,
    led="VERMELHO"
):

    global dados_sistema

    with trava:

        dados_sistema = {
            "status": status,
            "x": int(x),
            "y": int(y),
            "erroX": int(erro_x),
            "angulo": int(ANGULO_ATUAL),
            "led": led,
            "detectado": bool(detectado)
        }


# ==========================================
# INICIAR ESTADO DOS COMPONENTES
# ==========================================

atualizar_leds(
    vermelho=True,
    amarelo=False,
    verde=False
)

controlar_servo(90)

# ==========================================
# CONECTAR CAMERA
# ==========================================

print("Conectando a camera ESP32...")

camera = cv2.VideoCapture(URL_CAMERA)

if not camera.isOpened():

    print("ERRO: Nao foi possivel abrir a camera!")

    arduino.close()

    raise SystemExit

print("Camera conectada!")
print("SPL PROJECT INICIADO!")

# ==========================================
# INICIAR SERVIDOR WEB
# ==========================================

def iniciar_site():

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True
    )


servidor = threading.Thread(
    target=iniciar_site,
    daemon=True
)

servidor.start()

print("Dashboard disponivel em:")
print("http://127.0.0.1:5000")

# ==========================================
# LOOP PRINCIPAL DE PROCESSAMENTO
# ==========================================

try:

    while True:

        sucesso, frame = camera.read()

        if not sucesso:

            print("Erro ao receber imagem da camera.")

            atualizar_dados(
                status="ERRO NA CAMERA"
            )

            break

        # Padronizar a imagem para 320x240
        frame = cv2.resize(
            frame,
            (LARGURA_VIDEO, ALTURA_VIDEO)
        )

        altura, largura = frame.shape[:2]

        centro_tela = largura // 2

        # Converter para escala de cinza
        cinza = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        # Detectar pixels muito luminosos
        _, mascara = cv2.threshold(
            cinza,
            LIMIAR_LUZ,
            255,
            cv2.THRESH_BINARY
        )

        # Encontrar regioes luminosas
        contornos, _ = cv2.findContours(
            mascara,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        regioes = [
            c for c in contornos
            if cv2.contourArea(c) >= AREA_MINIMA
        ]

        # Valores iniciais de cada quadro
        x = 0
        y = 0
        erro_x = 0
        detectado = False
        status = "PROCURANDO LUZ"
        led_atual = "VERMELHO"

        # ==================================
        # SE ENCONTRAR UMA REGIAO LUMINOSA
        # ==================================

        if regioes:

            regiao = max(
                regioes,
                key=cv2.contourArea
            )

            momentos = cv2.moments(regiao)

            if momentos["m00"] != 0:

                x = int(
                    momentos["m10"] /
                    momentos["m00"]
                )

                y = int(
                    momentos["m01"] /
                    momentos["m00"]
                )

                erro_x = x - centro_tela

                detectado = True

                # Converter posicao em angulo
                angulo_alvo = int(
                    (x / (largura - 1)) * 180
                )

                if ANGULO_INVERTIDO:

                    angulo_alvo = 180 - angulo_alvo

                diferenca = (
                    angulo_alvo - ANGULO_ATUAL
                )

                # ==================================
                # RASTREAMENTO
                # ==================================

                if abs(erro_x) > TOLERANCIA:

                    atualizar_leds(
                        vermelho=False,
                        amarelo=True,
                        verde=False
                    )

                    led_atual = "AMARELO"

                    if diferenca > 0:

                        novo_angulo = min(
                            ANGULO_ATUAL + VELOCIDADE_SERVO,
                            angulo_alvo
                        )

                    else:

                        novo_angulo = max(
                            ANGULO_ATUAL - VELOCIDADE_SERVO,
                            angulo_alvo
                        )

                    controlar_servo(novo_angulo)

                    status = "RASTREANDO"

                else:

                    atualizar_leds(
                        vermelho=False,
                        amarelo=False,
                        verde=True
                    )

                    led_atual = "VERDE"

                    status = "LUZ CENTRALIZADA"

                # Desenhar contorno
                cv2.drawContours(
                    frame,
                    [regiao],
                    -1,
                    (0, 255, 255),
                    2
                )

                # Desenhar ponto de deteccao
                cv2.circle(
                    frame,
                    (x, y),
                    6,
                    (0, 0, 255),
                    -1
                )

            else:

                atualizar_leds(
                    vermelho=True,
                    amarelo=False,
                    verde=False
                )

        # ==================================
        # NENHUMA LUZ ENCONTRADA
        # ==================================

        else:

            atualizar_leds(
                vermelho=True,
                amarelo=False,
                verde=False
            )

        # ==================================
        # DESENHAR REFERENCIA CENTRAL
        # ==================================

        cv2.line(
            frame,
            (centro_tela, 0),
            (centro_tela, altura),
            (255, 0, 0),
            1
        )

        cv2.line(
            frame,
            (0, altura // 2),
            (largura, altura // 2),
            (0, 255, 0),
            1
        )

        # Informacoes sobre a imagem
        cv2.putText(
            frame,
            status,
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1
        )

        cv2.putText(
            frame,
            f"X: {x} | SERVO: {ANGULO_ATUAL}",
            (10, 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1
        )

        # ==================================
        # ATUALIZAR DADOS DO SITE
        # ==================================

        atualizar_dados(
            status=status,
            x=x,
            y=y,
            erro_x=erro_x,
            detectado=detectado,
            led=led_atual
        )

        # ==================================
        # PREPARAR VIDEO PARA O NAVEGADOR
        # ==================================

        sucesso_jpg, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 80]
        )

        if sucesso_jpg:

            with trava:

                ultimo_frame = buffer.tobytes()

# ==========================================
# ENCERRAMENTO
# ==========================================

except KeyboardInterrupt:

    print("Encerramento solicitado pelo usuario.")

finally:

    print("Encerrando SPL Project...")

    camera.release()

    try:

        atualizar_leds(
            vermelho=False,
            amarelo=False,
            verde=False
        )

    except Exception as erro:

        print("Erro ao desligar LEDs:", erro)

    arduino.close()

    print("Sistema encerrado!")
