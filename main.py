
from ultralytics import YOLO
import cv2

modelo = YOLO("yolo26n.pt")
resultados = modelo("bus.jpg")

for resultado in resultados:

    imagem = resultado.orig_img.copy()

    print("Dimensões originais:", resultado.orig_shape)
    print("Formato da imagem:", imagem.shape)

    pessoas = []

    # Máscara branca inicial
    altura, largura = imagem.shape[:2]
    mascara = 255 * (imagem[:, :, 0] * 0 + 1)
    mascara = mascara.astype("uint8")

    for objeto in resultado.boxes:

        classe = int(objeto.cls[0])
        confianca = float(objeto.conf[0])
        nome = modelo.names[classe]

        x1, y1, x2, y2 = map(
            int, objeto.xyxy[0].tolist()
        )

        if nome == "person":

            pessoas.append((x1, y1, x2, y2))

            # Impede coordenadas fora da imagem
            x1 = max(0, min(x1, largura))
            x2 = max(0, min(x2, largura))
            y1 = max(0, min(y1, altura))
            y2 = max(0, min(y2, altura))

            # Apaga a região da pessoa na máscara
            mascara[y1:y2, x1:x2] = 0

            cv2.rectangle(
                imagem,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

    imagem_filtrada = cv2.bitwise_and(
        imagem,
        imagem,
        mask=mascara
    )

    cv2.imwrite("pessoas_detectadas.jpg", imagem)
    cv2.imwrite("mascara_pessoas.jpg", mascara)
    cv2.imwrite("imagem_filtrada.jpg", imagem_filtrada)

    print("\nTotal de pessoas:", len(pessoas))
    print("Máscara salva:", "mascara_pessoas.jpg")
    print("Imagem filtrada salva:", "imagem_filtrada.jpg")
