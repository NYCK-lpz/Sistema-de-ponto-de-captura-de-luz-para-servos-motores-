
import cv2
import serial
import time
import threading

from flask import Flask, Response, jsonify, send_from_directory
import os

# =========================================
# 1. CONFIGURACOES DO PROJETO
# =========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

URL_CAMERA = "http://10.0.1.11  :81/stream"

PORTA_ARDUINO = "COM5"
BAUD_RATE = 9600

LIMIAR_LUZ = 220
AREA_MINIMA = 20
TOLERANCIA = 12

ANGULO_ATUAL = 90
VELOCIDADE_SERVO = 3
ANGULO_INVERTIDO = False

# =========================================
# 2. CONFIGURACAO DO FLASK
# =========================================

app = Flask(__name__)

ultimo_frame = None

trava = threading.Lock()

dados_sistema = {
    "status": "Iniciando",
    "x": 0,
    "y": 0,
    "erroX": 0,
    "angulo": 90,
    "led": "Vermelho",
    "detectado": False
}

# =========================================
# 3. CONEXAO COM O ARDUINO
# =========================================

print("Conectando ao Arduino...")

arduino = serial.Serial(
    PORTA_ARDUINO,
    BAUD_RATE,
    timeout=1
)

time.sleep(2)

print("Arduino conectado!")

# Estados dos LEDs
estado_leds = {
    "VERMELHO": None,
    "AMARELO": None,
    "VERDE": None
}

# Estado do buzzer
estado_buzzer = None

# =========================================
# 4. ENVIO DE COMANDOS
# =========================================

def enviar_comando(comando):

    try:

        arduino.write((comando + "\n").encode("utf-8"))

        print("Comando enviado:", comando)

    except Exception as erro:

        print("Erro ao enviar comando:", erro)


# =========================================
# 5. CONTROLE DOS LEDS
# =========================================

def controlar_led(nome, ligado):

    global estado_leds

    if estado_leds[nome] != ligado:

        estado = "ON" if ligado else "OFF"

        comando = f"LED:{nome}:{estado}"

        enviar_comando(comando)

        estado_leds[nome] = ligado


# =========================================
# 6. CONTROLE DO BUZZER
# =========================================

def controlar_buzzer(ligado):

    global estado_buzzer

    if estado_buzzer != ligado:

        if ligado:

            enviar_comando("BUZZER:ON")

        else:

            enviar_comando("BUZZER:OFF")

        estado_buzzer = ligado


# =========================================
# 7. CONTROLE DO SERVO MOTOR
# =========================================

def controlar_servo(angulo):

    global ANGULO_ATUAL

    diferenca = angulo - ANGULO_ATUAL

    if abs(diferenca) > VELOCIDADE_SERVO:

        if diferenca > 0:

            ANGULO_ATUAL += VELOCIDADE_SERVO

        else:

            ANGULO_ATUAL -= VELOCIDADE_SERVO

    else:

        ANGULO_ATUAL = angulo

    ANGULO_ATUAL = max(0, min(180, ANGULO_ATUAL))

    enviar_comando(f"SERVO:{ANGULO_ATUAL}")


# =========================================
# 8. ATUALIZACAO DOS LEDS E BUZZER
# =========================================

def atualizar_leds(vermelho, amarelo, verde):

    controlar_led("VERMELHO", vermelho)

    controlar_led("AMARELO", amarelo)

    controlar_led("VERDE", verde)

    # O buzzer acompanha o LED vermelho
    controlar_buzzer(vermelho)


# =========================================
# 9. ROTAS DO PAINEL WEB
# =========================================

@app.route("/")
def pagina_inicial():

    return send_from_directory(BASE_DIR, "index.html")


@app.route("/style.css")
def carregar_css():

    return send_from_directory(BASE_DIR, "style.css")


@app.route("/script.js")
def carregar_javascript():

    return send_from_directory(BASE_DIR, "script.js")


@app.route("/api/status")
def api_status():

    with trava:

        return jsonify(dados_sistema.copy())


# =========================================
# 10. TRANSMISSAO DO VIDEO
# =========================================

def gerar_video():

    global ultimo_frame

    while True:

        with trava:

            frame = ultimo_frame

        if frame is None:

            time.sleep(0.05)

            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame
            + b"\r\n"
        )


@app.route("/video_feed")
def video_feed():

    return Response(
        gerar_video(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# =========================================
# 11. INICIAR SERVIDOR WEB
# =========================================

def iniciar_servidor():

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True
    )


servidor = threading.Thread(
    target=iniciar_servidor,
    daemon=True
)

servidor.start()

print("Painel web iniciado!")
print("Acesse: http://127.0.0.1:5000")


# =========================================
# 12. CONECTAR A CAMERA ESP32
# =========================================

print("Conectando a camera...")

camera = cv2.VideoCapture(URL_CAMERA, cv2.CAP_FFMPEG)

if not camera.isOpened():

    print("ERRO: Nao foi possivel conectar a camera.")

    atualizar_leds(False, False, False)

    controlar_buzzer(False)

    arduino.close()

    raise SystemExit


print("Camera conectada!")


# =========================================
# 13. ESTADO INICIAL DO PROJETO
# =========================================

atualizar_leds(True, False, False)

print("SPL PROJECT EM FUNCIONAMENTO!")
print("Procurando fonte de luz...")


# =========================================
# 14. PROCESSAMENTO DA IMAGEM
# =========================================

try:

    while True:

        sucesso, frame = camera.read()

        if not sucesso:

            print("Falha ao receber imagem da camera.")

            time.sleep(0.1)

            continue

        # Redimensionar imagem
        frame = cv2.resize(frame, (320, 240))

        altura, largura = frame.shape[:2]

        # Centro da imagem
        CENTRO_X = largura // 2
        CENTRO_Y = altura // 2

        # Converter para escala de cinza
        cinza = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        # Identificar pixels muito claros
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

        regioes_validas = []

        for contorno in contornos:

            area = cv2.contourArea(contorno)

            if area >= AREA_MINIMA:

                regioes_validas.append(contorno)

        detectado = False

        x = 0
        y = 0
        erro_x = 0

        # =================================
        # 15. ANALISE DA FONTE DE LUZ
        # =================================

        if regioes_validas:

            # Selecionar maior regiao luminosa
            maior_contorno = max(
                regioes_validas,
                key=cv2.contourArea
            )

            momentos = cv2.moments(maior_contorno)

            if momentos["m00"] != 0:

                x = int(
                    momentos["m10"] / momentos["m00"]
                )

                y = int(
                    momentos["m01"] / momentos["m00"]
                )

                detectado = True

                erro_x = CENTRO_X - x

                # Desenhar contorno
                cv2.drawContours(
                    frame,
                    [maior_contorno],
                    -1,
                    (0, 255, 255),
                    2
                )

                # Marcar centro da luz
                cv2.circle(
                    frame,
                    (x, y),
                    6,
                    (0, 0, 255),
                    -1
                )

        # =================================
        # 16. CONTROLE DO SERVO E DOS LEDS
        # =================================

        if detectado:

            # Calcular angulo desejado
            angulo_desejado = int(
                (x / largura) * 180
            )

            if ANGULO_INVERTIDO:

                angulo_desejado = 180 - angulo_desejado

            angulo_desejado = max(
                0,
                min(180, angulo_desejado)
            )

            controlar_servo(angulo_desejado)

            # Luz proxima do centro
            if abs(erro_x) <= TOLERANCIA:

                status = "Luz centralizada"

                led_ativo = "Verde"

                atualizar_leds(
                    False,
                    False,
                    True
                )

            else:

                status = "Acompanhando luz"

                led_ativo = "Amarelo"

                atualizar_leds(
                    False,
                    True,
                    False
                )

        else:

            status = "Procurando luz"

            led_ativo = "Vermelho"

            atualizar_leds(
                True,
                False,
                False
            )

        # =================================
        # 17. DESENHAR INFORMACOES NA IMAGEM
        # =================================

        # Eixo horizontal
        cv2.line(
            frame,
            (0, CENTRO_Y),
            (largura, CENTRO_Y),
            (0, 255, 0),
            1
        )

        # Eixo vertical
        cv2.line(
            frame,
            (CENTRO_X, 0),
            (CENTRO_X, altura),
            (0, 255, 0),
            1
        )

        # Centro da imagem
        cv2.circle(
            frame,
            (CENTRO_X, CENTRO_Y),
            5,
            (0, 255, 255),
            -1
        )

        # Informacoes na imagem
        cv2.putText(
            frame,
            status,
            (5, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )

        cv2.putText(
            frame,
            f"Servo: {ANGULO_ATUAL}",
            (5, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )

        # =================================
        # 18. ATUALIZAR DADOS DO PAINEL
        # =================================

        with trava:

            dados_sistema.update({

                "status": status,

                "x": int(x),

                "y": int(y),

                "erroX": int(erro_x),

                "angulo": int(ANGULO_ATUAL),

                "led": led_ativo,

                "detectado": bool(detectado)

            })

        # =================================
        # 19. ENVIAR IMAGEM PARA O PAINEL
        # =================================

        sucesso_jpg, buffer = cv2.imencode(
            ".jpg",
            frame
        )

        if sucesso_jpg:

            with trava:

                ultimo_frame = buffer.tobytes()

        time.sleep(0.03)


# =========================================
# 20. ENCERRAMENTO DO SISTEMA
# =========================================

except KeyboardInterrupt:

    print("\nEncerrando SPL Project...")


finally:

    camera.release()

    atualizar_leds(
        False,
        False,
        False
    )

    controlar_buzzer(False)

    if arduino.is_open:

        arduino.close()

    print("Camera desconectada.")

    print("Arduino desconectado.")

    print("Buzzer desligado.")

    print("SPL Project encerrado.")
