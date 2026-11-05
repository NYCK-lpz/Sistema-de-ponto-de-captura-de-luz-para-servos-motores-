
from ultralytics import YOLO

# Carrega o modelo
modelo = YOLO("yolo26n.pt")

# Analisa a imagem de teste
resultados = modelo("bus.jpg")

# Percorre os resultados
for resultado in resultados:

    for objeto in resultado.boxes:

        # Identifica a classe
        classe = int(objeto.cls[0])
        confianca = float(objeto.conf[0])
        nome = modelo.names[classe]

        # Obtém as coordenadas da caixa
        x1, y1, x2, y2 = objeto.xyxy[0].tolist()

        # Calcula o centro do objeto
        centro_x = (x1 + x2) / 2
        centro_y = (y1 + y2) / 2

        print(f"Objeto: {nome}")
        print(f"Confiança: {confianca:.2%}")

        print(f"X inicial: {x1:.1f}")
        print(f"Y inicial: {y1:.1f}")
        print(f"X final: {x2:.1f}")
        print(f"Y final: {y2:.1f}")

        print(f"Centro X: {centro_x:.1f}")
        print(f"Centro Y: {centro_y:.1f}")

        print("-------------------------")
