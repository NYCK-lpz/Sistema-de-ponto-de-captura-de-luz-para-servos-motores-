import cv2

URL_CAMERA = "http://192.168.0.49:81/stream"

camera = cv2.VideoCapture(URL_CAMERA)

if not camera.isOpened():
    print("Erro ao conectar com a câmera!")
    exit()

print("Câmera conectada com sucesso!")

while True:
    sucesso, frame = camera.read()

    if not sucesso:
        print("Erro ao receber imagem.")
        break

    cv2.imshow("Camera ESP32 - Teste", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()