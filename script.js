
const canvas = document.getElementById("overlay");
const ctx = canvas.getContext("2d");

const conexao = document.getElementById("conexao");

const status = document.getElementById("status");
const posX = document.getElementById("posX");
const posY = document.getElementById("posY");
const erroX = document.getElementById("erroX");
const angulo = document.getElementById("angulo");
const led = document.getElementById("led");
const deteccao = document.getElementById("deteccao");

// Centro da imagem
const CENTRO_X = 160;
const CENTRO_Y = 120;

// Desenha os elementos visuais
function desenharMonitor(dados) {

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Eixo horizontal
    ctx.beginPath();
    ctx.moveTo(0, CENTRO_Y);
    ctx.lineTo(320, CENTRO_Y);
    ctx.strokeStyle = "#00ff88";
    ctx.lineWidth = 1;
    ctx.stroke();

    // Eixo vertical
    ctx.beginPath();
    ctx.moveTo(CENTRO_X, 0);
    ctx.lineTo(CENTRO_X, 240);
    ctx.stroke();

    // Centro da câmera
    ctx.beginPath();
    ctx.arc(CENTRO_X, CENTRO_Y, 5, 0, Math.PI * 2);
    ctx.fillStyle = "#ffff00";
    ctx.fill();

    // Posição da luz detectada
    if (dados.detectado) {

        ctx.beginPath();

        ctx.arc(
            dados.x,
            dados.y,
            6,
            0,
            Math.PI * 2
        );

        ctx.fillStyle = "#ff3333";
        ctx.fill();

        // Linha ligando o centro ao alvo
        ctx.beginPath();
        ctx.moveTo(CENTRO_X, CENTRO_Y);
        ctx.lineTo(dados.x, dados.y);
        ctx.strokeStyle = "#ff3333";
        ctx.stroke();
    }
}

// Busca informações do Python
async function atualizarPainel() {

    try {

        const resposta = await fetch("/api/status");

        if (!resposta.ok) {
            throw new Error("Servidor indisponível");
        }

        const dados = await resposta.json();

        conexao.textContent = "Sistema conectado";

        status.textContent = dados.status ?? "Aguardando";

        posX.textContent = dados.x ?? 0;

        posY.textContent = dados.y ?? 0;

        erroX.textContent = dados.erroX ?? 0;

        angulo.textContent = `${dados.angulo ?? 90}°`;

        led.textContent = dados.led ?? "Nenhum";

        deteccao.textContent = dados.detectado
            ? "Luz detectada"
            : "Procurando luz";

        desenharMonitor(dados);

    } catch (erro) {

        conexao.textContent = "Sistema desconectado";

        status.textContent = "Sem comunicação";

    }
}

// Atualiza os dados a cada 200 ms
setInterval(atualizarPainel, 200);

// Primeira atualização
atualizarPainel();
