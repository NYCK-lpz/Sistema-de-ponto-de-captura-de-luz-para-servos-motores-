
from ultralytics import YOLO
import cv2
import numpy as np

# ==============================
# CONFIGURAÇÕES
# ==============================

LIMIAR_BRILHO = 220
AREA_MINIMA = 10

# ==============================
# CARREGAR MODELO E IMAGEM
# ==============================

modelo = YOLO("yolo26n.pt")
resultados = modelo("bus.jpg")

for resultado in resultados:

    imagem = resultado.orig_img.copy()
    visualizacao = imagem.copy()

    altura, largura = imagem.shape[:2]

    # Cria máscara inicialmente branca
    mascara = np.full(
        (altura, largura),
        255,
        dtype=np.uint8
    )

    pessoas = []

    # ==============================
    # IDENTIFICAR PESSOAS
    # ==============================

    for objeto in resultado.boxes:

        classe = int(objeto.cls[0])
        nome = modelo.names[classe]
        confianca = float(objeto.conf[0])

        if nome == "person":

            x1, y1, x2, y2 = map(
                int, objeto.xyxy[0].tolist()
            )

            # Limita coordenadas à imagem
            x1 = max(0, min(x1, largura))
            x2 = max(0, min(x2, largura))
            y1 = max(0, min(y1, altura))
            y2 = max(0, min(y2, altura))

            pessoas.append((x1, y1, x2, y2))

            # Bloqueia a região da pessoa
            mascara[y1:y2, x1:x2] = 0

            cv2.rectangle(
                visualizacao,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

    # ==============================
    # ANALISAR LUMINOSIDADE
    # ==============================

    # Converte imagem colorida para tons de cinza
    cinza = cv2.cvtColor(
        imagem,
        cv2.COLOR_BGR2GRAY
    )

    # Seleciona pixels com brilho acima do limite
    _, imagem_luminosa = cv2.threshold(
        cinza,
        LIMIAR_BRILHO,
        255,
        cv2.THRESH_BINARY
    )

    # Ignora regiões bloqueadas pelo YOLO
    luminosidade_filtrada = cv2.bitwise_and(
        imagem_luminosa,
        imagem_luminosa,
        mask=mascara
    )

    # ==============================
    # LOCALIZAR PONTOS LUMINOSOS
    # ==============================

    contornos, _ = cv2.findContours(
        luminosidade_filtrada,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    quantidade_pontos = 0

    for contorno in contornos:

        area = cv2.contourArea(contorno)

        if area < AREA_MINIMA:
            continue

        momentos = cv2.moments(contorno)

        if momentos["m00"] == 0:
            continue

        centro_x = int(
            momentos["m10"] / momentos["m00"]
        )

        centro_y = int(
            momentos["m01"] / momentos["m00"]
        )

        quantidade_pontos += 1

        # Desenha o ponto luminoso
        cv2.circle(
            visualizacao,
            (centro_x, centro_y),
            6,
            (0, 0, 255),
            -1
        )

        cv2.putText(
            visualizacao,
            f"X:{centro_x} Y:{centro_y}",
            (centro_x + 10, centro_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            2
        )

        print(
            f"Ponto luminoso: X={centro_x}, Y={centro_y}"
        )

    # ==============================
    # SALVAR RESULTADOS
    # ==============================

    cv2.imwrite("mascara_pessoas.jpg", mascara)

    cv2.imwrite(
        "luminosidade_filtrada.jpg",
        luminosidade_filtrada
    )

    cv2.imwrite(
        "resultado_luminosidade.jpg",
        visualizacao
    )

    print("\n========== RESULTADO ==========")
    print("Pessoas identificadas:", len(pessoas))
    print("Regioes luminosas encontradas:", quantidade_pontos)
    print("Imagem processada e salva!")
