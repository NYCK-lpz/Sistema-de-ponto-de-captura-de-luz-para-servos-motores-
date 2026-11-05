
from ultralytics import YOLO
import cv2

# Carrega o modelo de inteligência artificial
modelo = YOLO("yolo26n.pt")

# Analisa a imagem
resultados = modelo("bus.jpg")

for resultado in resultados:

    imagem = resultado.orig_img.copy()
    print("Dimensões originais:", resultado.orig_shape)
    print("Formato da imagem:", imagem.shape)

    # Lista que armazenará as regiões das pessoas
    pessoas = []

    for objeto in resultado.boxes:

        classe = int(objeto.cls[0])
        confianca = float(objeto.conf[0])
        nome = modelo.names[classe]

        # Obtém as coordenadas do objeto
        x1, y1, x2, y2 = map(
            int, objeto.xyxy[0].tolist()
        )

        # Verifica se o objeto é uma pessoa
        if nome == "person":

            pessoas.append((x1, y1, x2, y2))

            cv2.rectangle(
                imagem,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.putText(
                imagem,
                f"Pessoa {confianca:.0%}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

    print("\nPESSOAS IDENTIFICADAS:")

    for pessoa in pessoas:
        print(f"Regiao: {pessoa}")

    print(f"\nTotal de pessoas: {len(pessoas)}")

    cv2.imwrite("pessoas_detectadas.jpg", imagem)

print("\nImagem salva como pessoas_detectadas.jpg")
