import cv2

for indice in range(4):
    camera = cv2.VideoCapture(indice, cv2.CAP_DSHOW)

    if camera.isOpened():
        sucesso, frame = camera.read()

        if sucesso:
            altura, largura = frame.shape[:2]
            print(f"Indice {indice}: funciona ({largura}x{altura})")
        else:
            print(f"Indice {indice}: abre, mas nao entrega imagem")

        camera.release()
    else:
        print(f"Indice {indice}: nao abre")