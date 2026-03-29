"""HTML5 Canvas game generator.

Template-based generation for browser-playable games. Produces a
self-contained HTML file with inline CSS + JavaScript using HTML5 Canvas.
No external dependencies required.

Mirrors the genre and difficulty structure of generator.py (Pygame version).
"""

from __future__ import annotations

import html as _html


def _sanitize_title(title: str) -> str:
    """Escape a game title for safe embedding in HTML and JS strings."""
    # HTML-escape first, then escape JS string delimiters
    safe = _html.escape(title, quote=True)
    safe = safe.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")
    return safe


# Difficulty presets per genre (same as Pygame generator)
DIFFICULTY_PARAMS: dict[str, dict[str, dict]] = {
    "shooter": {
        "easy": {"enemy_speed": 2, "spawn_interval": 1500},
        "medium": {"enemy_speed": 3, "spawn_interval": 1000},
        "hard": {"enemy_speed": 5, "spawn_interval": 600},
    },
    "puzzle": {
        "easy": {"grid_size": 4},
        "medium": {"grid_size": 6},
        "hard": {"grid_size": 8},
    },
    "sports": {
        "easy": {"ball_speed": 4, "paddle_speed": 5},
        "medium": {"ball_speed": 6, "paddle_speed": 6},
        "hard": {"ball_speed": 8, "paddle_speed": 7},
    },
    "platformer": {
        "easy": {"player_speed": 4},
        "medium": {"player_speed": 5},
        "hard": {"player_speed": 6},
    },
}


# ---------------------------------------------------------------------------
# HTML5 Canvas templates
# ---------------------------------------------------------------------------

_SHOOTER_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 100%; height: 100%; overflow: hidden; background: #000; }}
canvas {{ display: block; margin: 0 auto; background: #000; }}
</style>
</head>
<body>
<canvas id="game"></canvas>
<script>
(function() {{
"use strict";
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

function resize() {{
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}}
window.addEventListener("resize", resize);
resize();

const ENEMY_SPEED = {enemy_speed};
const SPAWN_INTERVAL = {spawn_interval};
const PLAYER_SPEED = 6;
const BULLET_SPEED = 8;
const TITLE = "{title}";

let state = "title"; // title | playing | gameover
let score = 0;
let player, bullets, enemies, spawnTimer, lastTime;
const keys = {{}};

function initGame() {{
    player = {{ x: canvas.width / 2 - 25, y: canvas.height - 80, w: 50, h: 50 }};
    bullets = [];
    enemies = [];
    spawnTimer = 0;
    score = 0;
    lastTime = performance.now();
}}

function spawnEnemy() {{
    const x = Math.random() * (canvas.width - 40) + 20;
    enemies.push({{ x: x, y: -40, w: 40, h: 40 }});
}}

function rectsCollide(a, b) {{
    return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}}

document.addEventListener("keydown", function(e) {{
    keys[e.code] = true;
    if (e.code === "Space") e.preventDefault();
    if (state === "title" && e.code === "Space") {{
        state = "playing";
        initGame();
    }}
    if (state === "playing" && e.code === "Space") {{
        bullets.push({{ x: player.x + player.w / 2 - 3, y: player.y, w: 6, h: 12 }});
    }}
    if (state === "gameover" && e.code === "KeyR") {{
        state = "playing";
        initGame();
    }}
}});
document.addEventListener("keyup", function(e) {{ keys[e.code] = false; }});

function update(dt) {{
    if (state !== "playing") return;

    if (keys["ArrowLeft"] && player.x > 0) player.x -= PLAYER_SPEED;
    if (keys["ArrowRight"] && player.x + player.w < canvas.width) player.x += PLAYER_SPEED;

    for (let i = bullets.length - 1; i >= 0; i--) {{
        bullets[i].y -= BULLET_SPEED;
        if (bullets[i].y + bullets[i].h < 0) bullets.splice(i, 1);
    }}

    spawnTimer += dt;
    if (spawnTimer >= SPAWN_INTERVAL) {{
        spawnEnemy();
        spawnTimer = 0;
    }}

    for (let i = enemies.length - 1; i >= 0; i--) {{
        enemies[i].y += ENEMY_SPEED;
        if (enemies[i].y > canvas.height) {{
            state = "gameover";
            return;
        }}
    }}

    for (let bi = bullets.length - 1; bi >= 0; bi--) {{
        for (let ei = enemies.length - 1; ei >= 0; ei--) {{
            if (rectsCollide(bullets[bi], enemies[ei])) {{
                bullets.splice(bi, 1);
                enemies.splice(ei, 1);
                score += 10;
                break;
            }}
        }}
    }}

    for (let i = 0; i < enemies.length; i++) {{
        if (rectsCollide(player, enemies[i])) {{
            state = "gameover";
            return;
        }}
    }}
}}

function draw() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (state === "title") {{
        ctx.fillStyle = "#0ff";
        ctx.font = "bold 48px monospace";
        ctx.textAlign = "center";
        ctx.fillText(TITLE, canvas.width / 2, canvas.height / 2 - 40);
        ctx.fillStyle = "#fff";
        ctx.font = "24px monospace";
        ctx.fillText("Arrow Keys to move, Space to shoot", canvas.width / 2, canvas.height / 2 + 20);
        ctx.fillStyle = "#888";
        ctx.font = "20px monospace";
        ctx.fillText("Press SPACE to start", canvas.width / 2, canvas.height / 2 + 70);
        return;
    }}

    // Player
    ctx.fillStyle = "#0ff";
    ctx.fillRect(player.x, player.y, player.w, player.h);

    // Bullets
    ctx.fillStyle = "#fff";
    for (const b of bullets) ctx.fillRect(b.x, b.y, b.w, b.h);

    // Enemies
    ctx.fillStyle = "#ff3232";
    for (const e of enemies) ctx.fillRect(e.x, e.y, e.w, e.h);

    // Score
    ctx.fillStyle = "#fff";
    ctx.font = "24px monospace";
    ctx.textAlign = "left";
    ctx.fillText("Score: " + score, 10, 30);

    if (state === "gameover") {{
        ctx.fillStyle = "rgba(0,0,0,0.6)";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = "#ff3232";
        ctx.font = "bold 48px monospace";
        ctx.textAlign = "center";
        ctx.fillText("GAME OVER", canvas.width / 2, canvas.height / 2 - 20);
        ctx.fillStyle = "#fff";
        ctx.font = "24px monospace";
        ctx.fillText("Score: " + score, canvas.width / 2, canvas.height / 2 + 30);
        ctx.fillStyle = "#888";
        ctx.font = "20px monospace";
        ctx.fillText("Press R to restart", canvas.width / 2, canvas.height / 2 + 70);
    }}
}}

function loop(now) {{
    const dt = now - lastTime;
    lastTime = now;
    update(dt);
    draw();
    requestAnimationFrame(loop);
}}

initGame();
lastTime = performance.now();
requestAnimationFrame(loop);
}})();
</script>
</body>
</html>'''

_PUZZLE_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 100%; height: 100%; overflow: hidden; background: #000; }}
canvas {{ display: block; margin: 0 auto; background: #000; cursor: pointer; }}
</style>
</head>
<body>
<canvas id="game"></canvas>
<script>
(function() {{
"use strict";
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const GRID_SIZE = {grid_size};
const COLORS = ["#ff5050", "#50ff50", "#5050ff", "#ffff50", "#ff50ff", "#50ffff"];
const TITLE = "{title}";

let state = "title"; // title | playing
let grid, selected, score, moves, cellSize, offsetX, offsetY, animating;

function resize() {{
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const boardSize = Math.min(canvas.width, canvas.height - 80) * 0.85;
    cellSize = Math.floor(boardSize / GRID_SIZE);
    offsetX = Math.floor((canvas.width - cellSize * GRID_SIZE) / 2);
    offsetY = Math.floor((canvas.height - cellSize * GRID_SIZE) / 2) + 20;
}}
window.addEventListener("resize", resize);
resize();

function initGame() {{
    grid = [];
    for (let r = 0; r < GRID_SIZE; r++) {{
        grid[r] = [];
        for (let c = 0; c < GRID_SIZE; c++) {{
            grid[r][c] = Math.floor(Math.random() * COLORS.length);
        }}
    }}
    selected = null;
    score = 0;
    moves = 0;
    animating = false;
    // Clear initial matches
    while (findMatches().length > 0) {{
        removeMatches(findMatches());
        dropAndFill();
    }}
}}

function findMatches() {{
    const matched = new Set();
    // Horizontal
    for (let r = 0; r < GRID_SIZE; r++) {{
        for (let c = 0; c < GRID_SIZE - 2; c++) {{
            const val = grid[r][c];
            if (val !== -1 && grid[r][c+1] === val && grid[r][c+2] === val) {{
                let end = c + 2;
                while (end + 1 < GRID_SIZE && grid[r][end+1] === val) end++;
                for (let k = c; k <= end; k++) matched.add(r * GRID_SIZE + k);
            }}
        }}
    }}
    // Vertical
    for (let c = 0; c < GRID_SIZE; c++) {{
        for (let r = 0; r < GRID_SIZE - 2; r++) {{
            const val = grid[r][c];
            if (val !== -1 && grid[r+1][c] === val && grid[r+2][c] === val) {{
                let end = r + 2;
                while (end + 1 < GRID_SIZE && grid[end+1][c] === val) end++;
                for (let k = r; k <= end; k++) matched.add(k * GRID_SIZE + c);
            }}
        }}
    }}
    return Array.from(matched);
}}

function removeMatches(matches) {{
    for (const idx of matches) {{
        const r = Math.floor(idx / GRID_SIZE);
        const c = idx % GRID_SIZE;
        grid[r][c] = -1;
    }}
    score += matches.length * 10;
}}

function dropAndFill() {{
    for (let c = 0; c < GRID_SIZE; c++) {{
        let writeRow = GRID_SIZE - 1;
        for (let r = GRID_SIZE - 1; r >= 0; r--) {{
            if (grid[r][c] !== -1) {{
                grid[writeRow][c] = grid[r][c];
                if (writeRow !== r) grid[r][c] = -1;
                writeRow--;
            }}
        }}
        for (let r = writeRow; r >= 0; r--) {{
            grid[r][c] = Math.floor(Math.random() * COLORS.length);
        }}
    }}
}}

function processMatches() {{
    let m = findMatches();
    while (m.length > 0) {{
        removeMatches(m);
        dropAndFill();
        m = findMatches();
    }}
}}

function swap(r1, c1, r2, c2) {{
    const tmp = grid[r1][c1];
    grid[r1][c1] = grid[r2][c2];
    grid[r2][c2] = tmp;
}}

canvas.addEventListener("click", function(e) {{
    if (state === "title") {{
        state = "playing";
        initGame();
        return;
    }}
    const mx = e.clientX - canvas.getBoundingClientRect().left;
    const my = e.clientY - canvas.getBoundingClientRect().top;
    const c = Math.floor((mx - offsetX) / cellSize);
    const r = Math.floor((my - offsetY) / cellSize);
    if (r < 0 || r >= GRID_SIZE || c < 0 || c >= GRID_SIZE) return;

    if (selected === null) {{
        selected = [r, c];
    }} else {{
        const [sr, sc] = selected;
        if (Math.abs(sr - r) + Math.abs(sc - c) === 1) {{
            swap(sr, sc, r, c);
            const m = findMatches();
            if (m.length > 0) {{
                processMatches();
                moves++;
            }} else {{
                swap(sr, sc, r, c); // swap back
            }}
        }}
        selected = null;
    }}
}});

document.addEventListener("keydown", function(e) {{
    if (state === "playing" && e.code === "KeyR") {{
        initGame();
    }}
    if (state === "title" && e.code === "Space") {{
        state = "playing";
        initGame();
    }}
}});

function draw() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (state === "title") {{
        ctx.fillStyle = "#0ff";
        ctx.font = "bold 48px monospace";
        ctx.textAlign = "center";
        ctx.fillText(TITLE, canvas.width / 2, canvas.height / 2 - 40);
        ctx.fillStyle = "#fff";
        ctx.font = "24px monospace";
        ctx.fillText("Click to select and swap adjacent tiles", canvas.width / 2, canvas.height / 2 + 20);
        ctx.fillText("Match 3 or more to score!", canvas.width / 2, canvas.height / 2 + 55);
        ctx.fillStyle = "#888";
        ctx.font = "20px monospace";
        ctx.fillText("Click or press SPACE to start", canvas.width / 2, canvas.height / 2 + 100);
        return;
    }}

    // Draw grid
    for (let r = 0; r < GRID_SIZE; r++) {{
        for (let c = 0; c < GRID_SIZE; c++) {{
            const x = offsetX + c * cellSize + 2;
            const y = offsetY + r * cellSize + 2;
            const s = cellSize - 4;
            ctx.fillStyle = COLORS[grid[r][c]] || "#333";
            ctx.beginPath();
            ctx.roundRect(x, y, s, s, 8);
            ctx.fill();
            if (selected && selected[0] === r && selected[1] === c) {{
                ctx.strokeStyle = "#fff";
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.roundRect(x, y, s, s, 8);
                ctx.stroke();
            }}
        }}
    }}

    // HUD
    ctx.fillStyle = "#fff";
    ctx.font = "24px monospace";
    ctx.textAlign = "left";
    ctx.fillText("Score: " + score + "  Moves: " + moves, 10, 30);
    ctx.textAlign = "right";
    ctx.fillStyle = "#888";
    ctx.font = "16px monospace";
    ctx.fillText("Press R to restart", canvas.width - 10, 30);
}}

function loop() {{
    draw();
    requestAnimationFrame(loop);
}}

initGame();
requestAnimationFrame(loop);
}})();
</script>
</body>
</html>'''

_SPORTS_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 100%; height: 100%; overflow: hidden; background: #000; }}
canvas {{ display: block; margin: 0 auto; background: #000; }}
</style>
</head>
<body>
<canvas id="game"></canvas>
<script>
(function() {{
"use strict";
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

function resize() {{
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}}
window.addEventListener("resize", resize);
resize();

const BALL_SPEED = {ball_speed};
const PADDLE_SPEED = {paddle_speed};
const PADDLE_W = 15;
const PADDLE_H = 100;
const BALL_SIZE = 12;
const TITLE = "{title}";

let state = "title";
let leftPaddle, rightPaddle, ball, ballDx, ballDy, scoreLeft, scoreRight;
const keys = {{}};

function initGame() {{
    leftPaddle = {{ x: 30, y: canvas.height / 2 - PADDLE_H / 2, w: PADDLE_W, h: PADDLE_H }};
    rightPaddle = {{ x: canvas.width - 45, y: canvas.height / 2 - PADDLE_H / 2, w: PADDLE_W, h: PADDLE_H }};
    scoreLeft = 0;
    scoreRight = 0;
    resetBall();
}}

function resetBall() {{
    ball = {{ x: canvas.width / 2 - BALL_SIZE / 2, y: canvas.height / 2 - BALL_SIZE / 2, w: BALL_SIZE, h: BALL_SIZE }};
    const angle = (Math.random() * Math.PI / 3) - Math.PI / 6;
    const dir = Math.random() < 0.5 ? 1 : -1;
    ballDx = BALL_SPEED * dir * Math.cos(angle);
    ballDy = BALL_SPEED * Math.sin(angle);
}}

function rectsCollide(a, b) {{
    return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}}

document.addEventListener("keydown", function(e) {{
    keys[e.code] = true;
    if (["ArrowUp", "ArrowDown", "Space"].includes(e.code)) e.preventDefault();
    if (state === "title" && e.code === "Space") {{
        state = "playing";
        initGame();
    }}
    if (state === "playing" && e.code === "KeyR") {{
        initGame();
    }}
}});
document.addEventListener("keyup", function(e) {{ keys[e.code] = false; }});

function update() {{
    if (state !== "playing") return;

    // Left paddle (W/S)
    if (keys["KeyW"] && leftPaddle.y > 0) leftPaddle.y -= PADDLE_SPEED;
    if (keys["KeyS"] && leftPaddle.y + leftPaddle.h < canvas.height) leftPaddle.y += PADDLE_SPEED;

    // Right paddle (Up/Down)
    if (keys["ArrowUp"] && rightPaddle.y > 0) rightPaddle.y -= PADDLE_SPEED;
    if (keys["ArrowDown"] && rightPaddle.y + rightPaddle.h < canvas.height) rightPaddle.y += PADDLE_SPEED;

    // Update right paddle position if window resized
    rightPaddle.x = canvas.width - 45;

    // Ball movement
    ball.x += ballDx;
    ball.y += ballDy;

    // Top/bottom bounce
    if (ball.y <= 0) {{ ball.y = 0; ballDy = Math.abs(ballDy); }}
    if (ball.y + ball.h >= canvas.height) {{ ball.y = canvas.height - ball.h; ballDy = -Math.abs(ballDy); }}

    // Paddle collision
    if (rectsCollide(ball, leftPaddle) && ballDx < 0) {{
        ballDx = Math.abs(ballDx);
        const hitPos = (ball.y + ball.h / 2 - leftPaddle.y) / leftPaddle.h - 0.5;
        ballDy = hitPos * BALL_SPEED * 1.5;
    }}
    if (rectsCollide(ball, rightPaddle) && ballDx > 0) {{
        ballDx = -Math.abs(ballDx);
        const hitPos = (ball.y + ball.h / 2 - rightPaddle.y) / rightPaddle.h - 0.5;
        ballDy = hitPos * BALL_SPEED * 1.5;
    }}

    // Scoring
    if (ball.x + ball.w < 0) {{
        scoreRight++;
        resetBall();
    }}
    if (ball.x > canvas.width) {{
        scoreLeft++;
        resetBall();
    }}
}}

function draw() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (state === "title") {{
        ctx.fillStyle = "#0ff";
        ctx.font = "bold 48px monospace";
        ctx.textAlign = "center";
        ctx.fillText(TITLE, canvas.width / 2, canvas.height / 2 - 40);
        ctx.fillStyle = "#fff";
        ctx.font = "24px monospace";
        ctx.fillText("Left: W/S    Right: Up/Down", canvas.width / 2, canvas.height / 2 + 20);
        ctx.fillStyle = "#888";
        ctx.font = "20px monospace";
        ctx.fillText("Press SPACE to start", canvas.width / 2, canvas.height / 2 + 70);
        return;
    }}

    // Center line
    ctx.setLineDash([8, 8]);
    ctx.strokeStyle = "#444";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(canvas.width / 2, 0);
    ctx.lineTo(canvas.width / 2, canvas.height);
    ctx.stroke();
    ctx.setLineDash([]);

    // Paddles
    ctx.fillStyle = "#fff";
    ctx.fillRect(leftPaddle.x, leftPaddle.y, leftPaddle.w, leftPaddle.h);
    ctx.fillRect(rightPaddle.x, rightPaddle.y, rightPaddle.w, rightPaddle.h);

    // Ball
    ctx.fillStyle = "#0ff";
    ctx.beginPath();
    ctx.arc(ball.x + ball.w / 2, ball.y + ball.h / 2, ball.w / 2, 0, Math.PI * 2);
    ctx.fill();

    // Score
    ctx.fillStyle = "#fff";
    ctx.font = "bold 48px monospace";
    ctx.textAlign = "center";
    ctx.fillText(scoreLeft + "  " + scoreRight, canvas.width / 2, 50);

    // Restart hint
    ctx.fillStyle = "#555";
    ctx.font = "14px monospace";
    ctx.fillText("Press R to restart", canvas.width / 2, canvas.height - 15);
}}

function loop() {{
    update();
    draw();
    requestAnimationFrame(loop);
}}

initGame();
requestAnimationFrame(loop);
}})();
</script>
</body>
</html>'''

_PLATFORMER_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 100%; height: 100%; overflow: hidden; background: #000; }}
canvas {{ display: block; margin: 0 auto; background: #000; }}
</style>
</head>
<body>
<canvas id="game"></canvas>
<script>
(function() {{
"use strict";
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

function resize() {{
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}}
window.addEventListener("resize", resize);
resize();

const PLAYER_SPEED = {player_speed};
const GRAVITY = 0.6;
const JUMP_POWER = -13;
const TITLE = "{title}";

let state = "title";
let player, velY, onGround, score, platforms, coins;
const keys = {{}};

function initGame() {{
    const w = canvas.width;
    const h = canvas.height;
    player = {{ x: 100, y: h - 140, w: 32, h: 48 }};
    velY = 0;
    onGround = false;
    score = 0;

    platforms = [
        {{ x: 0, y: h - 40, w: w, h: 40 }},                      // ground
        {{ x: w * 0.2, y: h - 160, w: 160, h: 20 }},
        {{ x: w * 0.5, y: h - 240, w: 160, h: 20 }},
        {{ x: w * 0.15, y: h - 340, w: 160, h: 20 }},
        {{ x: w * 0.55, y: h - 420, w: 200, h: 20 }},
        {{ x: w * 0.3, y: h - 520, w: 140, h: 20 }},
        {{ x: w * 0.7, y: h - 320, w: 140, h: 20 }},
    ];

    coins = [
        {{ x: w * 0.27, y: h - 190, w: 16, h: 16 }},
        {{ x: w * 0.57, y: h - 270, w: 16, h: 16 }},
        {{ x: w * 0.22, y: h - 370, w: 16, h: 16 }},
        {{ x: w * 0.63, y: h - 450, w: 16, h: 16 }},
        {{ x: w * 0.37, y: h - 550, w: 16, h: 16 }},
        {{ x: w * 0.75, y: h - 350, w: 16, h: 16 }},
    ];
}}

function rectsCollide(a, b) {{
    return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}}

document.addEventListener("keydown", function(e) {{
    keys[e.code] = true;
    if (["ArrowUp", "ArrowDown", "Space"].includes(e.code)) e.preventDefault();
    if (state === "title" && e.code === "Space") {{
        state = "playing";
        initGame();
    }}
    if (state === "playing" && e.code === "Space" && onGround) {{
        velY = JUMP_POWER;
        onGround = false;
    }}
    if (state === "gameover" && e.code === "KeyR") {{
        state = "playing";
        initGame();
    }}
}});
document.addEventListener("keyup", function(e) {{ keys[e.code] = false; }});

function update() {{
    if (state !== "playing") return;

    let dx = 0;
    if (keys["ArrowLeft"]) dx = -PLAYER_SPEED;
    if (keys["ArrowRight"]) dx = PLAYER_SPEED;
    player.x += dx;
    player.x = Math.max(0, Math.min(canvas.width - player.w, player.x));

    velY += GRAVITY;
    player.y += velY;

    onGround = false;
    for (const p of platforms) {{
        if (rectsCollide(player, p) && velY >= 0) {{
            player.y = p.y - player.h;
            velY = 0;
            onGround = true;
        }}
    }}

    // Fell off screen
    if (player.y > canvas.height + 100) {{
        state = "gameover";
        return;
    }}

    for (let i = coins.length - 1; i >= 0; i--) {{
        if (rectsCollide(player, coins[i])) {{
            coins.splice(i, 1);
            score += 25;
        }}
    }}

    if (coins.length === 0) {{
        state = "gameover";
    }}
}}

function draw() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (state === "title") {{
        ctx.fillStyle = "#0ff";
        ctx.font = "bold 48px monospace";
        ctx.textAlign = "center";
        ctx.fillText(TITLE, canvas.width / 2, canvas.height / 2 - 40);
        ctx.fillStyle = "#fff";
        ctx.font = "24px monospace";
        ctx.fillText("Arrow Keys to move, Space to jump", canvas.width / 2, canvas.height / 2 + 20);
        ctx.fillText("Collect all the coins!", canvas.width / 2, canvas.height / 2 + 55);
        ctx.fillStyle = "#888";
        ctx.font = "20px monospace";
        ctx.fillText("Press SPACE to start", canvas.width / 2, canvas.height / 2 + 100);
        return;
    }}

    // Platforms
    ctx.fillStyle = "#50c850";
    for (const p of platforms) {{
        ctx.fillRect(p.x, p.y, p.w, p.h);
    }}

    // Coins (gold circles with shimmer)
    for (const c of coins) {{
        ctx.fillStyle = "#ffd700";
        ctx.beginPath();
        ctx.arc(c.x + c.w / 2, c.y + c.h / 2, c.w / 2 + 2, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#ffec80";
        ctx.beginPath();
        ctx.arc(c.x + c.w / 2 - 2, c.y + c.h / 2 - 2, c.w / 4, 0, Math.PI * 2);
        ctx.fill();
    }}

    // Player
    ctx.fillStyle = "#0ff";
    ctx.fillRect(player.x, player.y, player.w, player.h);
    // Eyes
    ctx.fillStyle = "#000";
    ctx.fillRect(player.x + 8, player.y + 10, 5, 5);
    ctx.fillRect(player.x + 19, player.y + 10, 5, 5);

    // Score
    ctx.fillStyle = "#fff";
    ctx.font = "24px monospace";
    ctx.textAlign = "left";
    ctx.fillText("Score: " + score, 10, 30);

    // Coins remaining
    ctx.textAlign = "right";
    ctx.fillStyle = "#ffd700";
    ctx.fillText("Coins: " + coins.length, canvas.width - 10, 30);

    if (state === "gameover") {{
        ctx.fillStyle = "rgba(0,0,0,0.6)";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        const won = coins.length === 0;
        ctx.fillStyle = won ? "#ffd700" : "#ff3232";
        ctx.font = "bold 48px monospace";
        ctx.textAlign = "center";
        ctx.fillText(won ? "YOU WIN!" : "GAME OVER", canvas.width / 2, canvas.height / 2 - 20);
        ctx.fillStyle = "#fff";
        ctx.font = "24px monospace";
        ctx.fillText("Score: " + score, canvas.width / 2, canvas.height / 2 + 30);
        ctx.fillStyle = "#888";
        ctx.font = "20px monospace";
        ctx.fillText("Press R to restart", canvas.width / 2, canvas.height / 2 + 70);
    }}
}}

function loop() {{
    update();
    draw();
    requestAnimationFrame(loop);
}}

initGame();
requestAnimationFrame(loop);
}})();
</script>
</body>
</html>'''


# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------

HTML_TEMPLATES: dict[str, str] = {
    "shooter": _SHOOTER_TEMPLATE,
    "puzzle": _PUZZLE_TEMPLATE,
    "sports": _SPORTS_TEMPLATE,
    "platformer": _PLATFORMER_TEMPLATE,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_html_game(genre: str, title: str, difficulty: str = "medium") -> str:
    """Generate a self-contained HTML5 Canvas game. Returns HTML string.

    Args:
        genre: One of "shooter", "puzzle", "sports", "platformer".
        title: Game title displayed on the title screen.
        difficulty: One of "easy", "medium", "hard".

    Returns:
        Complete HTML string ready to serve or embed in an iframe.

    Raises:
        ValueError: If genre or difficulty is unknown.
    """
    template = HTML_TEMPLATES.get(genre)
    if template is None:
        raise ValueError(
            f"Unknown genre: {genre!r}. "
            f"Available: {', '.join(HTML_TEMPLATES.keys())}"
        )

    genre_params = DIFFICULTY_PARAMS.get(genre, {})
    params = genre_params.get(difficulty)
    if params is None:
        raise ValueError(
            f"Unknown difficulty: {difficulty!r} for genre {genre!r}. "
            f"Available: {', '.join(genre_params.keys())}"
        )

    return template.format(title=_sanitize_title(title), **params)


def get_html_controls(genre: str) -> dict[str, str]:
    """Get control descriptions for the HTML5 version of a genre.

    Args:
        genre: One of "shooter", "puzzle", "sports", "platformer".

    Returns:
        Dictionary mapping action names to key descriptions.
    """
    controls: dict[str, dict[str, str]] = {
        "shooter": {
            "move": "Arrow keys (left/right)",
            "shoot": "Space",
            "restart": "R",
        },
        "puzzle": {
            "select": "Mouse click",
            "swap": "Click adjacent tile",
            "restart": "R",
        },
        "sports": {
            "left_paddle": "W / S",
            "right_paddle": "Up / Down arrows",
            "restart": "R",
        },
        "platformer": {
            "move": "Arrow keys (left/right)",
            "jump": "Space",
            "restart": "R",
        },
    }
    return controls.get(genre, {})
