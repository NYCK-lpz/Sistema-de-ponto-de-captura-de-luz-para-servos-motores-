import time
import cv2

URL_CAMERA = "http://10.0.1.11:81/stream"

print("Conectando a camera...")
camera = cv2.VideoCapture(URL_CAMERA, cv2.CAP_FFMPEG)

if not camera.isOpened():
    print("ERRO: nao foi possivel conectar a camera.")
    raise SystemExit

print("Pressione Q na janela para encerrar.")

intervalos_ms = []
ultimo = time.perf_counter()

try:
    while True:
        sucesso, frame = camera.read()

        if not sucesso:
            time.sleep(0.1)
            continue

        agora = time.perf_counter()
        intervalo_ms = (agora - ultimo) * 1000
        ultimo = agora
        intervalos_ms.append(intervalo_ms)

        frame = cv2.resize(frame, (320, 240))

        fps = 1000 / max(intervalo_ms, 1)

        cv2.putText(
            frame,
            f"{fps:.0f} FPS",
            (5, 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )

        cv2.imshow("Teste camera sem YOLO", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    camera.release()
    cv2.destroyAllWindows()

    validos = intervalos_ms[5:]

    if validos:
        media = sum(validos) / len(validos)
        print(f"Frames medidos: {len(validos)}")
        print(f"Intervalo medio entre frames: {media:.0f} ms (~{1000 / media:.1f} FPS)")
        print(f"Menor: {min(validos):.0f} ms | Maior: {max(validos):.0f} ms")