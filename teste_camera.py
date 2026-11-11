
import cv2
import time

URL_CAMERA = "http://192.168.0.49:81/stream"

print("Conectando à câmera...")

camera = cv2.VideoCapture(URL_CAMERA, cv2.CAP_FFMPEG)

if not camera.isOpened():
    print("ERRO: Não foi possível abrir a câmera.")
    exit()

print("Câmera conectada!")

while True:

    sucesso, frame = camera.read()

    if not sucesso or frame is None:
        print("Falha ao receber quadro. Tentando novamente...")
        time.sleep(0.2)
        continue

    cv2.imshow("SPL PROJECT - CAMERA", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
