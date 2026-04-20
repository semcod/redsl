<?php
/**
 * ReDSL — Refactoring Proposals (SaaS Panel)
 *
 * User receives an email with a link to this page.
 * They can select which proposals (tickets) they want to implement.
 *
 * Selection format: "1, 3, 7, 12-15, 24" or "all" or "everything under 15"
 */

declare(strict_types=1);

session_start();

// Load .env
function load_env(string $path): void {
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
load_env(__DIR__ . '/.env');

function env(string $key, string $default = ''): string {
    return (string)($_ENV[$key] ?? getenv($key) ?: $default);
}

// Demo data — in production loaded from database/API
$proposals = [
    ['id' => 1, 'title' => 'UserService class refactoring', 'file' => 'src/services/UserService.php', 'effort' => 'M', 'lines' => 150, 'price' => 10, 'priority' => 1, 'redsl_min' => 8],
    ['id' => 2, 'title' => 'Method extraction in PaymentController', 'file' => 'src/controllers/PaymentController.php', 'effort' => 'S', 'lines' => 80, 'price' => 10, 'priority' => 2, 'redsl_min' => 4],
    ['id' => 3, 'title' => 'Cyclomatic complexity reduction', 'file' => 'src/utils/Calculator.php', 'effort' => 'L', 'lines' => 320, 'price' => 10, 'priority' => 1, 'redsl_min' => 15],
    ['id' => 4, 'title' => 'Remove code duplication in validators', 'file' => 'src/validators/', 'effort' => 'M', 'lines' => 200, 'price' => 10, 'priority' => 2, 'redsl_min' => 10],
    ['id' => 5, 'title' => 'Improve naming and conventions', 'file' => 'src/models/', 'effort' => 'S', 'lines' => 120, 'price' => 10, 'priority' => 3, 'redsl_min' => 3],
    ['id' => 6, 'title' => 'Repository pattern refactoring', 'file' => 'src/repositories/', 'effort' => 'L', 'lines' => 450, 'price' => 10, 'priority' => 1, 'redsl_min' => 20],
    ['id' => 7, 'title' => 'Interface extraction', 'file' => 'src/contracts/', 'effort' => 'M', 'lines' => 180, 'price' => 10, 'priority' => 2, 'redsl_min' => 9],
    ['id' => 8, 'title' => 'Remove dead code', 'file' => 'src/legacy/', 'effort' => 'S', 'lines' => 90, 'price' => 10, 'priority' => 3, 'redsl_min' => 3],
];

// Handle form submission
$message = '';
$selectedIds = [];
$totalPrice = 0;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $selection = $_POST['selection'] ?? '';
    $customInput = trim($_POST['custom_input'] ?? '');

    // Parse selection
    if ($selection === 'all') {
        $selectedIds = array_column($proposals, 'id');
        $totalPrice = count($proposals) * 10;
    } elseif ($selection === 'under_15') {
        // All under $15 — all are $10 so same as all
        $selectedIds = array_column($proposals, 'id');
        $totalPrice = count($proposals) * 10;
    } elseif ($selection === 'custom' && $customInput) {
        // Parse "1, 3, 7, 12-15, 24"
        $selectedIds = parseSelection($customInput);
        $totalPrice = count($selectedIds) * 10;
    }

    if (!empty($selectedIds)) {
        $message = sprintf(
            "Selected %d tickets. Total: $%d. Confirmation sent to email.",
            count($selectedIds),
            $totalPrice
        );
        // In production: save to database, send confirmation email
    }
}

function parseSelection(string $input): array {
    $ids = [];
    $parts = array_map('trim', explode(',', $input));

    foreach ($parts as $part) {
        if (strpos($part, '-') !== false) {
            // Range like "12-15"
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

function h(string $s): string {
    return htmlspecialchars($s, ENT_QUOTES | ENT_HTML5, 'UTF-8');
}

$priorityEmoji = [1 => '🔴', 2 => '🟠', 3 => '🟡'];
$humanHours = ['S' => '~2h', 'M' => '~4h', 'L' => '~8h'];

$year = date('Y');
$issue = date('Y.m');
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Refactoring Proposals — ReDSL</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&family=Instrument+Sans:ital,wght@0,400..700;1,400..700&family=JetBrains+Mono:wght@400;500;700&display=swap">
    <link rel="stylesheet" href="style.css">
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23c8442d'/%3E%3Ctext x='50%25' y='58%25' font-family='serif' font-size='22' fill='%23f4efe6' text-anchor='middle' font-weight='900'%3ER%3C/text%3E%3C/svg%3E">
    <style>
        * { box-sizing: border-box; }

        .lang-switch {
            text-align: right;
            margin-bottom: 8px;
            font-size: 12px;
        }
        .lang-switch a { color: #888; text-decoration: none; }
        .lang-switch a:hover { color: #c8442d; }
        .lang-switch .active { color: #1a1a2e; font-weight: 600; }

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

        .selection-panel {
            background: white;
            border-radius: 12px;
            padding: 24px 32px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .selection-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 16px;
            color: #333;
        }

        .option-row {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .option-row:hover {
            border-color: #3b82f6;
            background: #f8fafc;
        }
        .option-row input[type="radio"] {
            width: 20px;
            height: 20px;
            margin: 0;
        }
        .option-label {
            flex: 1;
            font-size: 14px;
        }
        .option-price {
            font-weight: 600;
            color: #c8442d;
        }

        .custom-input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 14px;
            font-family: 'SF Mono', Monaco, monospace;
            margin-top: 8px;
        }
        .custom-input:focus {
            outline: none;
            border-color: #3b82f6;
        }
        .hint {
            font-size: 12px;
            color: #666;
            margin-top: 6px;
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
            font-family: monospace;
            font-size: 13px;
            color: #666;
        }
        .prop-title {
            font-size: 14px;
            font-weight: 500;
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
            font-size: 12px;
            color: #666;
            text-align: right;
        }
        .prop-price {
            font-weight: 600;
            color: #c8442d;
            text-align: right;
        }

        .summary-bar {
            background: #1a1a2e;
            color: white;
            padding: 20px 32px;
            border-radius: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 20px;
        }
        .summary-text {
            font-size: 16px;
        }
        .summary-price {
            font-size: 28px;
            font-weight: 700;
        }
        .summary-note {
            font-size: 12px;
            opacity: 0.8;
            margin-top: 4px;
        }

        .btn-submit {
            padding: 14px 32px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            background: #3b82f6;
            color: white;
        }
        .btn-submit:hover {
            background: #2563eb;
        }

        .instructions {
            background: #fef3c7;
            border: 1px solid #fcd34d;
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .instructions strong {
            color: #92400e;
        }
        .instructions code {
            background: rgba(0,0,0,0.1);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
        }

        .help-text {
            text-align: center;
            margin-top: 30px;
            font-size: 13px;
            color: #888;
        }
        .help-text a {
            color: #3b82f6;
        }
    </style>
</head>
<body>

<!-- ============ MASTHEAD ============ -->
<header class="masthead">
    <div class="masthead-inner">
        <div class="masthead-left">
            <span class="issue">Issue <?=h($issue)?></span>
            <span class="dot">·</span>
            <span class="date"><?=h(date('j F Y'))?></span>
        </div>
        <a href="/" class="logo">
            <span class="logo-r">R</span><span>edsl</span>
        </a>
        <nav class="masthead-right">
            <a href="/#how">How it works</a>
            <a href="/#pricing">Pricing</a>
            <a href="/config-editor.php">Config</a>
            <a href="/proposals">Proposals</a>
            <a href="/#contact">Contact</a>
        </nav>
    </div>
    <div class="rule"></div>
</header>

<main class="proposals-container">
    <div class="lang-switch">
        <span class="active">EN</span>
        &nbsp;|&nbsp;
        <a href="/propozycje">PL</a>
    </div>

    <div class="page-header">
        <h1>Refactoring Proposals</h1>
        <p class="subtitle">Project: <strong>my-app</strong> · Received: <?=h(date('F j, Y'))?></p>
    </div>

    <?php if ($message): ?>
    <div class="alert"><?= h($message) ?></div>
    <?php endif; ?>

    <form method="post">
        <div class="instructions">
            <strong>How to select:</strong>
            <ul style="margin: 8px 0; padding-left: 20px;">
                <li><code>1, 3, 7</code> — select specific numbers (comma separated)</li>
                <li><code>12-15</code> — range from 12 to 15 inclusive</li>
                <li><code>all</code> — entire list</li>
                <li><code>everything under 15</code> — all tickets ($10 each)</li>
            </ul>
        </div>

        <div class="selection-panel">
            <div class="selection-title">Choose your tickets</div>

            <label class="option-row">
                <input type="radio" name="selection" value="all" checked>
                <span class="option-label">All proposals</span>
                <span class="option-price">$<?= count($proposals) * 10 ?></span>
            </label>

            <label class="option-row">
                <input type="radio" name="selection" value="under_15">
                <span class="option-label">Everything under $15 (all tickets)</span>
                <span class="option-price">$<?= count($proposals) * 10 ?></span>
            </label>

            <label class="option-row" style="flex-wrap: wrap;">
                <input type="radio" name="selection" value="custom">
                <span class="option-label" style="flex: 0 0 auto;">Custom selection:</span>
                <input type="text" name="custom_input" class="custom-input" placeholder="e.g. 1, 3, 7, 12-15, 24" style="flex: 1; min-width: 200px;">
            </label>
            <p class="hint">Each ticket: <strong>$10</strong> (up to 500 LOC, after PR merge)</p>
        </div>

        <div class="proposals-list">
            <div class="proposal-item" style="background: #fafafa; font-weight: 600; color: #666;">
                <div class="prop-id">ID</div>
                <div class="prop-title">Title / File</div>
                <div class="prop-effort" style="text-align:center">ReDSL</div>
                <div class="prop-effort" style="text-align:center">Human</div>
                <div class="prop-lines">Lines</div>
                <div class="prop-price">Price</div>
            </div>
            <?php foreach ($proposals as $p): ?>
            <div class="proposal-item">
                <div class="prop-id"><?= $p['id'] ?></div>
                <div>
                    <div class="prop-title"><?= h($p['title']) ?></div>
                    <div class="prop-file"><?= h($p['file']) ?></div>
                </div>
                <div class="prop-effort" style="text-align:center" title="ReDSL execution time"><?= $p['redsl_min'] ?> min</div>
                <div class="prop-effort" style="text-align:center; color:#888" title="Estimated manual effort"><?= $humanHours[$p['effort']] ?></div>
                <div class="prop-lines">~<?= $p['lines'] ?></div>
                <div class="prop-price">$<?= $p['price'] ?></div>
            </div>
            <?php endforeach; ?>
        </div>

        <div class="summary-bar">
            <div>
                <div class="summary-text">Select options above</div>
                <div class="summary-note">Payment after PR merge. NDA signed before scan.</div>
            </div>
            <button type="submit" class="btn-submit">Confirm selection →</button>
        </div>
    </form>

    <p class="help-text">
        Questions? <a href="/#contact">Contact us</a> or
        <a href="mailto:contact@redsl.io">contact@redsl.io</a>
    </p>
</main>

<!-- ============ FOOTER / KOLOPHON ============ -->
<footer class="colophon">
    <div class="container">
        <div class="colophon-grid">
            <div>
                <div class="footer-logo"><span class="logo-r">R</span>edsl</div>
                <p class="footer-sub">Refactor · DSL · Self-Learning</p>
            </div>
            <div>
                <h5>Product</h5>
                <ul>
                    <li><a href="/#how">How it works</a></li>
                    <li><a href="/#pricing">Pricing</a></li>
                    <li><a href="/#contact">Contact</a></li>
                </ul>
            </div>
            <div>
                <h5>Resources</h5>
                <ul>
                    <li><a href="https://github.com/wronai/redsl" rel="noopener">GitHub</a></li>
                    <li><a href="https://github.com/wronai/redsl/tree/main/docs" rel="noopener">Documentation</a></li>
                    <li><a href="/blog/">Blog</a></li>
                </ul>
            </div>
            <div>
                <h5>Legal</h5>
                <ul>
                    <li><a href="/nda-wzor">NDA Template</a></li>
                    <li><a href="/polityka-prywatnosci">Privacy</a></li>
                    <li><a href="/regulamin">Terms</a></li>
                </ul>
            </div>
        </div>
        <div class="colophon-bottom">
            <span>© <?=h((string)$year)?> ReDSL · Issue <?=h($issue)?></span>
            <span class="dot">·</span>
            <span>Poland · EU</span>
            <span class="dot">·</span>
            <span>Built in one night, maintained by one person.</span>
        </div>
    </div>
</footer>

<script src="app.js" defer></script>
</body>
</html>
