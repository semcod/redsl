<?php
/**
 * ReDSL — Regulamin / Terms of Service
 * i18n-aware, uses main site styling
 */
declare(strict_types=1);

$i18n = require __DIR__ . '/lib/i18n.php';
$t = $i18n['t'];
$lang = $i18n['lang']();
$getLangUrls = $i18n['getLangUrls'];
$getLangName = $i18n['getLangName'];

function h(string $s): string { return htmlspecialchars($s, ENT_QUOTES | ENT_HTML5, 'UTF-8'); }

$year = date('Y');
$issue = date('Y.m');
?>
<!DOCTYPE html>
<html lang="<?=h($lang)?>">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title><?=h($t('terms.page_title'))?></title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&family=Instrument+Sans:ital,wght@0,400..700;1,400..700&family=JetBrains+Mono:wght@400;500;700&display=swap">
<link rel="stylesheet" href="style.css">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23c8442d'/%3E%3Ctext x='50%25' y='58%25' font-family='serif' font-size='22' fill='%23f4efe6' text-anchor='middle' font-weight='900'%3ER%3C/text%3E%3C/svg%3E">
<style>
    .terms-container { max-width: 780px; margin: 0 auto; padding: 60px 20px 80px; }
    .terms-header { margin-bottom: 48px; }
    .terms-header h1 {
        font-family: var(--font-display);
        font-size: clamp(28px, 4vw, 40px);
        font-weight: 800;
        margin: 0 0 8px;
        color: var(--ink);
    }
    .terms-meta {
        font-size: 14px;
        color: var(--muted);
    }
    .terms-section { margin-bottom: 36px; }
    .terms-section h2 {
        font-family: var(--font-display);
        font-size: 22px;
        font-weight: 700;
        color: var(--ink);
        margin: 0 0 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--rule);
    }
    .terms-section p {
        color: var(--ink-soft);
        margin: 0 0 8px;
    }
    .terms-section .excludes {
        color: var(--muted);
        font-style: italic;
    }
    .terms-back {
        margin-top: 48px;
        padding-top: 24px;
        border-top: 1px solid var(--rule);
    }
    .terms-back a {
        color: var(--red);
        text-decoration: none;
        font-weight: 500;
    }
    .terms-back a:hover { text-decoration: underline; }
</style>
</head>
<body>

<header class="masthead">
    <div class="masthead-inner">
        <div class="masthead-left">
            <span class="issue"><?=h($t('meta.issue'))?> <?=h($issue)?></span>
            <span class="dot">·</span>
            <span class="date"><?=h(date('j F Y'))?></span>
        </div>
        <a href="/" class="logo">
            <span class="logo-r">R</span><span>edsl</span>
        </a>
        <nav class="masthead-right">
            <a href="/#jak"><?=h($t('nav.how_it_works'))?></a>
            <a href="/#cennik"><?=h($t('nav.pricing'))?></a>
            <a href="/#kontakt"><?=h($t('nav.contact'))?></a>
            <div class="lang-switcher">
                <?php foreach ($getLangUrls() as $code => $url): ?>
                    <?php if ($code === $lang): ?>
                        <span class="lang-current"><?=h(strtoupper($code))?></span>
                    <?php else: ?>
                        <a href="<?=h($url)?>" class="lang-link" title="<?=h($getLangName($code))?>"><?=h(strtoupper($code))?></a>
                    <?php endif; ?>
                <?php endforeach; ?>
            </div>
        </nav>
    </div>
    <div class="rule"></div>
</header>

<div class="terms-container">
    <div class="terms-header">
        <h1><?=h($t('terms.heading'))?></h1>
        <p class="terms-meta"><?=h($t('terms.updated'))?>: <?=h(date('j F Y'))?></p>
    </div>

    <div class="terms-section">
        <h2><?=h($t('terms.s1_title'))?></h2>
        <p><?=h($t('terms.s1_text'))?></p>
    </div>

    <div class="terms-section">
        <h2><?=h($t('terms.s2_title'))?></h2>
        <p><?=h($t('terms.s2_text'))?></p>
    </div>

    <div class="terms-section">
        <h2><?=h($t('terms.s3_title'))?></h2>
        <p><?=h($t('terms.s3_includes'))?></p>
        <p class="excludes"><?=h($t('terms.s3_excludes'))?></p>
    </div>

    <div class="terms-section">
        <h2><?=h($t('terms.s4_title'))?></h2>
        <p><?=h($t('terms.s4_text'))?></p>
    </div>

    <div class="terms-section">
        <h2><?=h($t('terms.s5_title'))?></h2>
        <p><?=h($t('terms.s5_text'))?></p>
    </div>

    <div class="terms-back">
        <a href="/"><?=h($t('terms.back'))?></a>
    </div>
</div>

<footer class="colophon">
    <div class="container">
        <div class="colophon-bottom">
            <span>&copy; <?=h((string)$year)?> REDSL &middot; <?=h($t('meta.issue'))?> <?=h($issue)?></span>
            <span class="dot">&middot;</span>
            <span>Polska &middot; UE</span>
        </div>
    </div>
</footer>

</body>
</html>
