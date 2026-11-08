
from ultralytics import YOLO
import cv2
import numpy as np

# =====================================
# 1. CONFIGURACOES
# =====================================

LIMIAR_BRILHO = 220
AREA_MINIMA = 10
LIMITE_REGIOES = 10

# =====================================
# 2. CARREGAR MODELO E IMAGEM
# =====================================

modelo = YOLO("yolo26n.pt")
resultados = modelo("bus.jpg")

for resultado in resultados:

    imagem = resultado.orig_img.copy()
    visualizacao = imagem.copy()

    altura, largura = imagem.shape[:2]

    print("Dimensoes da imagem:", largura, "x", altura)

    # =====================================
    # 3. CRIAR MASCARA
    # =====================================

    mascara = np.full(
        (altura, largura),
        255,
        dtype=np.uint8
    )

    pessoas = []

    # =====================================
    # 4. IDENTIFICAR PESSOAS COM YOLO
    # =====================================

    for objeto in resultado.boxes:

        classe = int(objeto.cls[0])
        nome = modelo.names[classe]

        if nome == "person":

            x1, y1, x2, y2 = map(
                int,
                objeto.xyxy[0].tolist()
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
    # 5. ANALISAR LUMINOSIDADE
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

    # Ignorar areas ocupadas por pessoas
    luminosidade_filtrada = cv2.bitwise_and(
        imagem_luminosa,
        imagem_luminosa,
        mask=mascara
    )

    # =====================================
    # 6. ENCONTRAR REGIOES LUMINOSAS
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

        # =====================================
        # 7. CALCULAR INTENSIDADE MEDIA
        # =====================================

        mascara_regiao = np.zeros_like(cinza)

        cv2.drawContours(
            mascara_regiao,
            [contorno],
            -1,
            255,
            -1
        )

        intensidade = cv2.mean(
            cinza,
            mask=mascara_regiao
        )[0]

        # =====================================
        # 8. ANALISAR FORMATO DA REGIAO
        # =====================================

        x, y, w, h = cv2.boundingRect(contorno)

        proporcao = w / h if h > 0 else 0

        regioes.append({
            "area": area,
            "x": centro_x,
            "y": centro_y,
            "intensidade": intensidade,
            "proporcao": proporcao
        })

    # =====================================
    # 9. CALCULAR PONTUACAO
    # =====================================

    maior_area = max(
        (regiao["area"] for regiao in regioes),
        default=1
    )

    for regiao in regioes:

        # Intensidade: 0 a 1
        pontuacao_intensidade = (
            regiao["intensidade"] / 255
        )

        # Formato: maior pontuacao para
        # regioes mais compactas
        proporcao = max(
            regiao["proporcao"],
            0.001
        )

        pontuacao_formato = (
            1 / (1 + abs(np.log(proporcao)))
        )

        # Area: 0 a 1
        pontuacao_area = (
            regiao["area"] / maior_area
        )

        # Pontuacao final: 0 a 100
        score = (
            pontuacao_intensidade * 0.50 +
            pontuacao_formato * 0.35 +
            pontuacao_area * 0.15
        ) * 100

        regiao["score"] = score

    # =====================================
    # 10. ORDENAR PELAS MAIORES PONTUACOES
    # =====================================

    regioes.sort(
        key=lambda regiao: regiao["score"],
        reverse=True
    )

    melhores_regioes = regioes[:LIMITE_REGIOES]

    # =====================================
    # 11. DESENHAR RESULTADOS
    # =====================================

    print("\nREGIOES LUMINOSAS CLASSIFICADAS:")

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
            f"X={x}, Y={y}, "
            f"Area={area:.0f}, "
            f"Intensidade={regiao['intensidade']:.1f}, "
            f"Proporcao={regiao['proporcao']:.2f}, "
            f"Score={regiao['score']:.2f}"
        )

    # =====================================
    # 12. SALVAR IMAGENS
    # =====================================

    cv2.imwrite(
        "mascara_pessoas.jpg",
        mascara
    )

    cv2.imwrite(
        "luminosidade_filtrada.jpg",
        luminosidade_filtrada
    )

    cv2.imwrite(
        "resultado_luminosidade.jpg",
        visualizacao
    )

    # =====================================
    # 13. RESUMO
    # =====================================

    print("\n========== RESULTADO ==========")

    print("Pessoas identificadas:", len(pessoas))
    print("Regioes encontradas:", len(regioes))
    print("Regioes classificadas:", len(melhores_regioes))

    if melhores_regioes:

        melhor = melhores_regioes[0]

        print("\nREGIAO MAIS BEM CLASSIFICADA:")
        print("Centro X:", melhor["x"])
        print("Centro Y:", melhor["y"])
        print("Pontuacao:", round(melhor["score"], 2))

    print("\nImagens salvas com sucesso!")
