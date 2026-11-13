import time
import cv2
from ultralytics import YOLO

URL_CAMERA = "http://10.0.1.11:81/stream"
CAMINHO_MODELO = "yolo26n.pt"

TAMANHO_INFERENCIA = 320   # resolucao usada pelo YOLO
CONFIANCA_MINIMA = 0.4     # ignora deteccoes abaixo de 40%
FRAMES_DE_AQUECIMENTO = 5  # as primeiras inferencias sao mais lentas

print("Carregando modelo YOLO...")
modelo = YOLO(CAMINHO_MODELO)

print("Conectando a camera...")

INDICE_CAMERA = 1
camera = cv2.VideoCapture(INDICE_CAMERA, cv2.CAP_DSHOW)

if not camera.isOpened():
    print("ERRO: nao foi possivel conectar a camera.")
    raise SystemExit

print("Pressione Q na janela para encerrar.")

tempos_ms = []

try:
    while True:
        sucesso, frame = camera.read()

        if not sucesso:
            time.sleep(0.1)
            continue

        frame = cv2.resize(frame, (320, 240))

        inicio = time.perf_counter()

        resultados = modelo(
            frame,
            imgsz=TAMANHO_INFERENCIA,
            conf=CONFIANCA_MINIMA,
            verbose=False
        )

        duracao_ms = (time.perf_counter() - inicio) * 1000
        tempos_ms.append(duracao_ms)

        for caixa in resultados[0].boxes:
            x1, y1, x2, y2 = map(int, caixa.xyxy[0].tolist())
            nome = modelo.names[int(caixa.cls[0])]
            confianca = float(caixa.conf[0])

            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 128, 0), 2)
            cv2.putText(
                frame,
                f"{nome} {confianca:.2f}",
                (x1, max(y1 - 5, 12)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 128, 0),
                1
            )

        cv2.putText(
            frame,
            f"YOLO: {duracao_ms:.0f} ms",
            (5, 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )

        cv2.imshow("Teste YOLO + camera", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    camera.release()
    cv2.destroyAllWindows()

    validos = tempos_ms[FRAMES_DE_AQUECIMENTO:]

    if validos:
        media = sum(validos) / len(validos)
        print(f"Inferencias medidas: {len(validos)}")
        print(f"Tempo medio: {media:.0f} ms (~{1000 / media:.1f} inferencias/s)")
        print(f"Mais rapida: {min(validos):.0f} ms | Mais lenta: {max(validos):.0f} ms")