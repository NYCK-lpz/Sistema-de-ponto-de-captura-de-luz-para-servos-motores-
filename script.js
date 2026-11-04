
// =====================================
// CONFIGURAÇÕES GERAIS
// =====================================

const canvas = document.getElementById("overlay");
const ctx = canvas.getContext("2d");

const camera = document.getElementById("stream");
const info = document.getElementById("info");

// Canvas oculto para processamento da imagem
const hiddenCanvas = document.createElement("canvas");
hiddenCanvas.width = 320;
hiddenCanvas.height = 240;

const hiddenCtx = hiddenCanvas.getContext("2d");

// =====================================
// CONFIGURAÇÕES DO SISTEMA
// =====================================

const LARGURA = 320;
const ALTURA = 240;

const CENTRO_X = 160;
const CENTRO_Y = 120;

const TOLERANCIA = 10;

// =====================================
// VARIÁVEIS
// =====================================

let pontoX = CENTRO_X;
let pontoY = CENTRO_Y;

let centralizado = false;

let servoXStatus = "PARADO";
let servoYStatus = "PARADO";

let anguloX = 90;
let anguloY = 90;

let quantidadePixels = 0;

let erroX = 0;
let erroY = 0;

// =====================================
// DESENHAR INTERFACE
// =====================================

function desenhar() {

    ctx.clearRect(0, 0, LARGURA, ALTURA);

    //---------------------------------
    // Eixos
    //---------------------------------

    ctx.lineWidth = 2;
    ctx.strokeStyle = "lime";

    ctx.beginPath();
    ctx.moveTo(CENTRO_X, 0);
    ctx.lineTo(CENTRO_X, ALTURA);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(0, CENTRO_Y);
    ctx.lineTo(LARGURA, CENTRO_Y);
    ctx.stroke();

    //---------------------------------
    // Zona de tolerância
    //---------------------------------

    ctx.strokeRect(
        CENTRO_X - TOLERANCIA,
        CENTRO_Y - TOLERANCIA,
        TOLERANCIA * 2,
        TOLERANCIA * 2
    );

    //---------------------------------
    // Centro
    //---------------------------------

    ctx.fillStyle = "yellow";

    ctx.beginPath();
    ctx.arc(CENTRO_X, CENTRO_Y, 4, 0, Math.PI * 2);
    ctx.fill();

    ctx.font = "14px Arial";

    ctx.fillText(
        "Centro",
        CENTRO_X + 10,
        CENTRO_Y - 8
    );

    //---------------------------------
    // Ponto rastreado
    //---------------------------------

    ctx.fillStyle = centralizado ? "lime" : "red";

    ctx.beginPath();
    ctx.arc(pontoX, pontoY, 6, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillText(
        `(${pontoX},${pontoY})`,
        pontoX + 10,
        pontoY
    );

    //---------------------------------
    // Informações
    //---------------------------------

    info.innerHTML = `
    <b>Rastreador Solar</b><br><br>

    X: ${pontoX}<br>
    Y: ${pontoY}<br>

    Erro X: ${erroX}<br>
    Erro Y: ${erroY}<br><br>

    Servo X: ${servoXStatus}<br>
    Servo Y: ${servoYStatus}<br><br>

    Ângulo X: ${anguloX}°<br>
    Ângulo Y: ${anguloY}°<br><br>

    Pixels Detectados: ${quantidadePixels}<br>

    Status:
    ${centralizado ? "🟢 CENTRALIZADO" : "🟡 AJUSTANDO"}
    `;
}

// Atualiza o desenho
setInterval(desenhar, 30);

// =====================================
// PROCESSAMENTO DA CÂMERA
// =====================================

setInterval(() => {

    // Copia o frame da câmera
    hiddenCtx.drawImage(
        camera,
        0,
        0,
        LARGURA,
        ALTURA
    );

    // Lê os pixels
    const frame = hiddenCtx.getImageData(
        0,
        0,
        LARGURA,
        ALTURA
    );

    //-------------------------------------
    // Variáveis do centro luminoso
    //-------------------------------------

    let somaX = 0;
    let somaY = 0;
    let quantidade = 0;

    //-------------------------------------
    // Percorre a imagem
    //-------------------------------------

    for (let y = 0; y < ALTURA; y += 2) {

        for (let x = 0; x < LARGURA; x += 2) {

            const indice = (y * LARGURA + x) * 4;

            const r = frame.data[indice];
            const g = frame.data[indice + 1];
            const b = frame.data[indice + 2];

            //---------------------------------
            // 1. Calcula o brilho
            //---------------------------------

            const brilho = (r + g + b) / 3;

            //---------------------------------
            // 2. Analisa a cor RGB
            //---------------------------------

            const maiorCanal = Math.max(r, g, b);
            const menorCanal = Math.min(r, g, b);

            const diferencaRGB = maiorCanal - menorCanal;

            //---------------------------------
            // 3. Critérios de detecção
            //---------------------------------

            const intensidadeAlta = brilho >= 220;

            const corNeutra = diferencaRGB <= 35;

            //---------------------------------
            // 4. Detecta pixels luminosos
            //---------------------------------

            if (intensidadeAlta && corNeutra) {

                somaX += x;
                somaY += y;

                quantidade++;
            }
        }
    }

    //-------------------------------------
    // Calcula o centro da mancha luminosa
    //-------------------------------------

    if (quantidade > 0) {

        const novoX = Math.round(somaX / quantidade);
        const novoY = Math.round(somaY / quantidade);

        //---------------------------------
        // Suavização
        //---------------------------------

        pontoX = Math.round(
            pontoX * 0.8 +
            novoX * 0.2
        );

        pontoY = Math.round(
            pontoY * 0.8 +
            novoY * 0.2
        );

        //---------------------------------
        // Calcula os erros
        //---------------------------------

        erroX = pontoX - CENTRO_X;
        erroY = pontoY - CENTRO_Y;

        //---------------------------------
        // Verifica centralização
        //---------------------------------

        centralizado =
            Math.abs(erroX) <= TOLERANCIA &&
            Math.abs(erroY) <= TOLERANCIA;

        //---------------------------------
        // Direção do Servo X
        //---------------------------------

        if (erroX > TOLERANCIA) {

            servoXStatus = "DIREITA";
            anguloX++;

        } else if (erroX < -TOLERANCIA) {

            servoXStatus = "ESQUERDA";
            anguloX--;

        } else {

            servoXStatus = "PARADO";
        }

        //---------------------------------
        // Direção do Servo Y
        //---------------------------------

        if (erroY > TOLERANCIA) {

            servoYStatus = "BAIXO";
            anguloY++;

        } else if (erroY < -TOLERANCIA) {

            servoYStatus = "CIMA";
            anguloY--;

        } else {

            servoYStatus = "PARADO";
        }

        //---------------------------------
        // Limita os ângulos
        //---------------------------------

        anguloX = Math.max(0, Math.min(180, anguloX));
        anguloY = Math.max(0, Math.min(180, anguloY));
    }

    //-------------------------------------
    // Atualiza quantidade de pixels
    //-------------------------------------

    quantidadePixels = quantidade;

}, 50);
