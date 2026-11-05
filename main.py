
from ultralytics import YOLO

# Carrega o modelo de reconhecimento
modelo = YOLO("yolo26n.pt")

# Executa um teste com uma imagem de exemplo
resultados = modelo("https://ultralytics.com/images/bus.jpg")

# Exibe os objetos identificados
for resultado in resultados:

    for objeto in resultado.boxes:

        classe = int(objeto.cls[0])
        confianca = float(objeto.conf[0])

        nome = modelo.names[classe]

        print(f"Objeto: {nome}")
        print(f"Confiança: {confianca:.2%}")
        print("-------------------")
