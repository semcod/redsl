<?php
/**
 * ReDSL — Propozycje Refaktoryzacji (Panel SaaS) — wersja PL
 *
 * Klient otrzymuje e-mail z linkiem do tej strony.
 * Może wybrać, które propozycje (tickety) chce zrealizować.
 *
 * Format wyboru: "1, 3, 7, 12-15, 24" lub "wszystkie" lub "wszystko pod 15"
 */

declare(strict_types=1);

session_start();

function load_env_pl(string $path): void {
    if (!is_readable($path)) return;
    foreach (file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $line = trim($line);
        if ($line === '' || str_starts_with($line, '#')) continue;
        if (!str_contains($line, '=')) continue;
        [$k, $v] = array_map('trim', explode('=', $line, 2));
        $v = trim($v, "\"'");
        $_ENV[$k] = $v;
    }
}
load_env_pl(__DIR__ . '/.env');

function env_pl(string $key, string $default = ''): string {
    return (string)($_ENV[$key] ?? getenv($key) ?: $default);
}

// Dane demo — w produkcji ładowane z bazy/API
$proposals = [
    ['id' => 1, 'title' => 'Refaktoryzacja klasy UserService', 'file' => 'src/services/UserService.php', 'effort' => 'M', 'lines' => 150, 'price' => 10, 'priority' => 1, 'redsl_min' => 8],
    ['id' => 2, 'title' => 'Ekstrakcja metod w PaymentController', 'file' => 'src/controllers/PaymentController.php', 'effort' => 'S', 'lines' => 80, 'price' => 10, 'priority' => 2, 'redsl_min' => 4],
    ['id' => 3, 'title' => 'Redukcja złożoności cyklomatycznej', 'file' => 'src/utils/Calculator.php', 'effort' => 'L', 'lines' => 320, 'price' => 10, 'priority' => 1, 'redsl_min' => 15],
    ['id' => 4, 'title' => 'Usunięcie duplikacji kodu w walidacjach', 'file' => 'src/validators/', 'effort' => 'M', 'lines' => 200, 'price' => 10, 'priority' => 2, 'redsl_min' => 10],
    ['id' => 5, 'title' => 'Poprawa nazewnictwa i konwencji', 'file' => 'src/models/', 'effort' => 'S', 'lines' => 120, 'price' => 10, 'priority' => 3, 'redsl_min' => 3],
    ['id' => 6, 'title' => 'Refaktoryzacja repository pattern', 'file' => 'src/repositories/', 'effort' => 'L', 'lines' => 450, 'price' => 10, 'priority' => 1, 'redsl_min' => 20],
    ['id' => 7, 'title' => 'Ekstrakcja interfejsów', 'file' => 'src/contracts/', 'effort' => 'M', 'lines' => 180, 'price' => 10, 'priority' => 2, 'redsl_min' => 9],
    ['id' => 8, 'title' => 'Usunięcie martwego kodu', 'file' => 'src/legacy/', 'effort' => 'S', 'lines' => 90, 'price' => 10, 'priority' => 3, 'redsl_min' => 3],
];

$message = '';
$selectedIds = [];
$totalPrice = 0;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $selection = $_POST['selection'] ?? '';
    $customInput = trim($_POST['custom_input'] ?? '');

    if ($selection === 'all') {
        $selectedIds = array_column($proposals, 'id');
        $totalPrice = count($proposals) * 10;
    } elseif ($selection === 'under_15') {
        $selectedIds = array_column($proposals, 'id');
        $totalPrice = count($proposals) * 10;
    } elseif ($selection === 'custom' && $customInput) {
        $selectedIds = parseSelection_pl($customInput);
        $totalPrice = count($selectedIds) * 10;
    }

    if (!empty($selectedIds)) {
        $message = sprintf(
            'Wybrano %d ticketów. Łącznie: %d zł. Potwierdzenie wysłane na e-mail.',
            count($selectedIds),
            $totalPrice
        );
    }
}

function parseSelection_pl(string $input): array {
    $ids = [];
    $parts = array_map('trim', explode(',', $input));
    foreach ($parts as $part) {
        if (strpos($part, '-') !== false) {
            [$start, $end] = array_map('intval', explode('-', $part));
            for ($i = $start; $i <= $end; $i++) {
                $ids[] = $i;
            }
        } else {
            $ids[] = intval($part);
        }
    }
    return array_unique(array_filter($ids));
}

function h_pl(string $s): string {
    return htmlspecialchars($s, ENT_QUOTES | ENT_HTML5, 'UTF-8');
}

$priorityEmoji = [1 => '🔴', 2 => '🟠', 3 => '🟡'];
$humanHours = ['S' => '~2h', 'M' => '~4h', 'L' => '~8h'];

$year = date('Y');
$issue = date('Y.m');
?>
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Propozycje Refaktoryzacji — ReDSL</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&family=Instrument+Sans:ital,wght@0,400..700;1,400..700&family=JetBrains+Mono:wght@400;500;700&display=swap">
    <link rel="stylesheet" href="style.css">
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23c8442d'/%3E%3Ctext x='50%25' y='58%25' font-family='serif' font-size='22' fill='%23f4efe6' text-anchor='middle' font-weight='900'%3ER%3C/text%3E%3C/svg%3E">
    <style>
        * { box-sizing: border-box; }

        .proposals-container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }

        .page-header {
            background: white;
            border-radius: 12px;
            padding: 24px 32px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .page-header h1 {
            margin: 0 0 8px 0;
            font-size: 24px;
            color: #1a1a2e;
        }
        .subtitle {
            color: #666;
            font-size: 14px;
        }

        .alert {
            background: #dcfce7;
            border: 1px solid #86efac;
            color: #166534;
            padding: 16px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }

        .instructions {
            background: white;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            font-size: 14px;
        }

        .selection-panel {
            background: white;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .selection-title {
            font-weight: 600;
            margin-bottom: 12px;
            color: #1a1a2e;
        }
        .option-row {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
            cursor: pointer;
        }
        .option-row:last-of-type { border-bottom: none; }
        .option-label { flex: 1; font-size: 14px; }
        .option-price { font-weight: 600; color: #c8442d; }
        .custom-input {
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 14px;
        }
        .hint {
            font-size: 12px;
            color: #888;
            margin-top: 12px;
        }

        .proposals-list {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .proposal-item {
            display: grid;
            grid-template-columns: 40px 1fr 80px 80px 70px 60px;
            gap: 16px;
            align-items: center;
            padding: 16px 24px;
            border-bottom: 1px solid #f0f0f0;
        }
        .proposal-item:last-child {
            border-bottom: none;
        }
        .proposal-item:hover {
            background: #fafafa;
        }
        .prop-id {
            font-weight: 600;
            color: #888;
            font-size: 13px;
        }
        .prop-title {
            font-weight: 500;
            font-size: 14px;
            color: #1a1a2e;
        }
        .prop-file {
            font-size: 12px;
            color: #888;
            margin-top: 2px;
        }
        .prop-effort {
            font-size: 12px;
            color: #666;
            text-align: center;
        }
        .prop-lines {
            font-size: 13px;
            color: #666;
            font-family: 'JetBrains Mono', monospace;
        }
        .prop-price {
            font-weight: 600;
            color: #c8442d;
        }

        .summary-bar {
            background: #1a1a2e;
            color: white;
            border-radius: 12px;
            padding: 20px 24px;
            margin-top: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
        }
        .summary-text {
            font-size: 16px;
            font-weight: 600;
        }
        .summary-note {
            font-size: 12px;
            color: #aaa;
            margin-top: 4px;
        }
        .btn-submit {
            background: #c8442d;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            white-space: nowrap;
        }
        .btn-submit:hover { background: #b03a25; }

        .help-text {
            text-align: center;
            color: #888;
            font-size: 13px;
            margin-top: 20px;
        }
        .help-text a { color: #c8442d; }

        .lang-switch {
            text-align: right;
            margin-bottom: 8px;
            font-size: 12px;
        }
        .lang-switch a { color: #888; text-decoration: none; }
        .lang-switch a:hover { color: #c8442d; }
        .lang-switch .active { color: #1a1a2e; font-weight: 600; }
    </style>
</head>
<body>

<header class="masthead">
    <div class="masthead-inner">
        <div class="masthead-left">
            <a href="/" class="logo"><span class="logo-r">R</span><span>edsl</span></a>
        </div>
        <nav class="masthead-right">
            <a href="/#jak">Jak działa</a>
            <a href="/#cennik">Cennik</a>
            <a href="/#kontakt">Kontakt</a>
        </nav>
    </div>
    <div class="rule"></div>
</header>

<main class="proposals-container">
    <div class="lang-switch">
        <a href="/proposals">EN</a>
        &nbsp;|&nbsp;
        <span class="active">PL</span>
    </div>

    <div class="page-header">
        <h1>Propozycje Refaktoryzacji</h1>
        <p class="subtitle">Projekt: <strong>my-app</strong> · Otrzymano: <?=h_pl(strftime('%d %B %Y') ?: date('d.m.Y'))?></p>
    </div>

    <?php if ($message): ?>
    <div class="alert"><?= h_pl($message) ?></div>
    <?php endif; ?>

    <form method="post">
        <div class="instructions">
            <strong>Jak wybrać:</strong>
            <ul style="margin: 8px 0; padding-left: 20px;">
                <li><code>1, 3, 7</code> — konkretne numery (oddzielone przecinkiem)</li>
                <li><code>12-15</code> — zakres od 12 do 15 włącznie</li>
                <li><code>wszystkie</code> — cała lista</li>
                <li><code>wszystko pod 15</code> — wszystkie tickety (po 10 zł)</li>
            </ul>
        </div>

        <div class="selection-panel">
            <div class="selection-title">Wybierz tickety</div>

            <label class="option-row">
                <input type="radio" name="selection" value="all" checked>
                <span class="option-label">Wszystkie propozycje</span>
                <span class="option-price"><?= count($proposals) * 10 ?> zł</span>
            </label>

            <label class="option-row">
                <input type="radio" name="selection" value="under_15">
                <span class="option-label">Wszystko pod 15 zł (tj. wszystkie)</span>
                <span class="option-price"><?= count($proposals) * 10 ?> zł</span>
            </label>

            <label class="option-row" style="flex-wrap: wrap;">
                <input type="radio" name="selection" value="custom">
                <span class="option-label" style="flex: 0 0 auto;">Własny wybór:</span>
                <input type="text" name="custom_input" class="custom-input" placeholder="np. 1, 3, 7, 12-15, 24" style="flex: 1; min-width: 200px;">
            </label>
            <p class="hint">Każdy ticket: <strong>10 zł</strong> (do 500 LOC, po zmergeowaniu PR)</p>
        </div>

        <div class="proposals-list">
            <div class="proposal-item" style="background: #fafafa; font-weight: 600; color: #666;">
                <div class="prop-id">ID</div>
                <div class="prop-title">Tytuł / Plik</div>
                <div class="prop-effort" style="text-align:center">ReDSL</div>
                <div class="prop-effort" style="text-align:center">Człowiek</div>
                <div class="prop-lines">Linie</div>
                <div class="prop-price">Cena</div>
            </div>
            <?php foreach ($proposals as $p): ?>
            <div class="proposal-item">
                <div class="prop-id"><?= $p['id'] ?></div>
                <div>
                    <div class="prop-title"><?= h_pl($p['title']) ?></div>
                    <div class="prop-file"><?= h_pl($p['file']) ?></div>
                </div>
                <div class="prop-effort" style="text-align:center" title="Czas wykonania przez ReDSL"><?= $p['redsl_min'] ?> min</div>
                <div class="prop-effort" style="text-align:center; color:#888" title="Szacowany czas ręczny"><?= $humanHours[$p['effort']] ?></div>
                <div class="prop-lines">~<?= $p['lines'] ?></div>
                <div class="prop-price"><?= $p['price'] ?> zł</div>
            </div>
            <?php endforeach; ?>
        </div>

        <div class="summary-bar">
            <div>
                <div class="summary-text">Wybierz opcje powyżej</div>
                <div class="summary-note">Płatność po zmergeowaniu PR. NDA podpisujemy przed skanem.</div>
            </div>
            <button type="submit" class="btn-submit">Potwierdź wybór →</button>
        </div>
    </form>

    <p class="help-text">
        Pytania? <a href="/#kontakt">Skontaktuj się</a> lub
        <a href="mailto:kontakt@redsl.io">kontakt@redsl.io</a>
    </p>
</main>

<!-- ============ FOOTER ============ -->
<footer class="colophon">
    <div class="container">
        <div class="colophon-grid">
            <div>
                <div class="footer-logo"><span class="logo-r">R</span>edsl</div>
                <p class="footer-sub">Refactor · DSL · Self-Learning</p>
            </div>
            <div>
                <h5>Produkt</h5>
                <ul>
                    <li><a href="/#jak">Jak działa</a></li>
                    <li><a href="/#cennik">Cennik</a></li>
                    <li><a href="/#kontakt">Kontakt</a></li>
                </ul>
            </div>
            <div>
                <h5>Zasoby</h5>
                <ul>
                    <li><a href="https://github.com/wronai/redsl" rel="noopener">GitHub</a></li>
                    <li><a href="https://github.com/wronai/redsl/tree/main/docs" rel="noopener">Dokumentacja</a></li>
                    <li><a href="/blog/">Blog</a></li>
                </ul>
            </div>
            <div>
                <h5>Prawne</h5>
                <ul>
                    <li><a href="/nda-wzor">Wzór NDA</a></li>
                    <li><a href="/polityka-prywatnosci">Prywatność</a></li>
                    <li><a href="/regulamin">Regulamin</a></li>
                </ul>
            </div>
        </div>
        <div class="colophon-bottom">
            <span>© <?=h_pl((string)$year)?> ReDSL · Wydanie <?=h_pl($issue)?></span>
            <span class="dot">·</span>
            <span>Polska · UE</span>
            <span class="dot">·</span>
            <span>Zbudowane w jedną noc, utrzymywane przez jedną osobę.</span>
        </div>
    </div>
</footer>

<script src="app.js" defer></script>
</body>
</html>
