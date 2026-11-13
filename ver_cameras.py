import cv2

camera0 = cv2.VideoCapture(0, cv2.CAP_DSHOW)
camera1 = cv2.VideoCapture(1, cv2.CAP_DSHOW)

print("Pressione Q para encerrar.")

try:
    while True:
        ok0, frame0 = camera0.read()
        ok1, frame1 = camera1.read()

        if ok0:
            cv2.putText(frame0, "INDICE 0", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Camera indice 0", frame0)

        if ok1:
            cv2.putText(frame1, "INDICE 1", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Camera indice 1", frame1)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    camera0.release()
    camera1.release()
    cv2.destroyAllWindows()