
from ultralytics import YOLO
import cv2

# Carrega o modelo
modelo = YOLO("yolo26n.pt")

# Analisa a imagem
resultados = modelo("bus.jpg")

# Percorre os resultados
for resultado in resultados:

    # Recupera a imagem original
    imagem = resultado.orig_img.copy()

    for objeto in resultado.boxes:

        classe = int(objeto.cls[0])
        confianca = float(objeto.conf[0])
        nome = modelo.names[classe]

        # Coordenadas na escala da imagem original
        x1, y1, x2, y2 = map(
            int, objeto.xyxy[0].tolist()
        )

        # Desenha a caixa
        cv2.rectangle(
            imagem,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        # Nome e confiança
        texto = f"{nome} {confianca:.0%}"

        cv2.putText(
            imagem,
            texto,
            (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    # Salva a imagem processada
    cv2.imwrite("resultado.jpg", imagem)

print("Imagem processada e salva como resultado.jpg")
