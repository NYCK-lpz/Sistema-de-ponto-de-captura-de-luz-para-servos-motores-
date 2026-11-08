
from ultralytics import YOLO
import cv2
import numpy as np

# =====================================
# CONFIGURACOES
# =====================================

LIMIAR_BRILHO = 220
AREA_MINIMA = 10
LIMITE_REGIOES = 10

# =====================================
# CARREGAR MODELO E IMAGEM
# =====================================

modelo = YOLO("yolo26n.pt")
resultados = modelo("bus.jpg")

for resultado in resultados:

    imagem = resultado.orig_img.copy()
    visualizacao = imagem.copy()

    altura, largura = imagem.shape[:2]

    print("Dimensoes da imagem:", largura, "x", altura)

    # =====================================
    # CRIAR MASCARA
    # =====================================

    mascara = np.full(
        (altura, largura),
        255,
        dtype=np.uint8
    )

    pessoas = []

    # =====================================
    # IDENTIFICAR PESSOAS COM YOLO
    # =====================================

    for objeto in resultado.boxes:

        classe = int(objeto.cls[0])
        nome = modelo.names[classe]
        confianca = float(objeto.conf[0])

        if nome == "person":

            x1, y1, x2, y2 = map(
                int, objeto.xyxy[0].tolist()
            )

            # Limitar coordenadas
            x1 = max(0, min(x1, largura))
            x2 = max(0, min(x2, largura))
            y1 = max(0, min(y1, altura))
            y2 = max(0, min(y2, altura))

            pessoas.append((x1, y1, x2, y2))

            # Bloquear pessoa na mascara
            mascara[y1:y2, x1:x2] = 0

            cv2.rectangle(
                visualizacao,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

    # =====================================
    # ANALISAR LUMINOSIDADE
    # =====================================

    cinza = cv2.cvtColor(
        imagem,
        cv2.COLOR_BGR2GRAY
    )

    _, imagem_luminosa = cv2.threshold(
        cinza,
        LIMIAR_BRILHO,
        255,
        cv2.THRESH_BINARY
    )

    # Ignorar pessoas
    luminosidade_filtrada = cv2.bitwise_and(
        imagem_luminosa,
        imagem_luminosa,
        mask=mascara
    )

    # =====================================
    # ENCONTRAR REGIOES LUMINOSAS
    # =====================================

    contornos, _ = cv2.findContours(
        luminosidade_filtrada,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    regioes = []

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

        regioes.append({
            "area": area,
            "x": centro_x,
            "y": centro_y
        })

    # =====================================
    # ORDENAR AS REGIOES
    # =====================================

    regioes.sort(
        key=lambda regiao: regiao["area"],
        reverse=True
    )

    melhores_regioes = regioes[:LIMITE_REGIOES]

    # =====================================
    # DESENHAR RESULTADOS
    # =====================================

    print("\nREGIOES LUMINOSAS:")

    for indice, regiao in enumerate(melhores_regioes):

        x = regiao["x"]
        y = regiao["y"]
        area = regiao["area"]

        cv2.circle(
            visualizacao,
            (x, y),
            6,
            (0, 0, 255),
            -1
        )

        cv2.putText(
            visualizacao,
            str(indice + 1),
            (x + 10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2
        )

        print(
            f"Regiao {indice + 1}: "
            f"X={x}, Y={y}, Area={area:.0f}"
        )

    # =====================================
    # SALVAR IMAGENS
    # =====================================

    cv2.imwrite("mascara_pessoas.jpg", mascara)

    cv2.imwrite(
        "luminosidade_filtrada.jpg",
        luminosidade_filtrada
    )

    cv2.imwrite(
        "resultado_luminosidade.jpg",
        visualizacao
    )

    # =====================================
    # RESUMO
    # =====================================

    print("\n========== RESULTADO ==========")
    print("Pessoas identificadas:", len(pessoas))
    print("Regioes encontradas:", len(regioes))
    print("Regioes exibidas:", len(melhores_regioes))
    print("Imagens salvas com sucesso!")
