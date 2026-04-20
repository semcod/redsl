<?php
declare(strict_types=1);
session_start();

// =============================================================
//  REDSL — Landing Page
//  Single-file PHP router: landing, contact form, GitHub OAuth
// =============================================================

/** Simple .env loader (no composer dependency) */
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

// ---- i18n ----
$i18n = require __DIR__ . '/lib/i18n.php';
$t = $i18n['t'];
$lang = $i18n['lang']();
$getLangUrls = $i18n['getLangUrls'];
$getLangName = $i18n['getLangName'];
$formatPrice = $i18n['formatPrice'];
$getPricing = $i18n['getPricing'];
$th = $i18n['th'];

// WORKAROUND: Override currency config based on URL language parameter
// (PHP OPcache prevents updates to i18n.php, so we detect currency here)
$currencyConfig = [
    'pl' => ['code' => 'PLN', 'symbol' => 'zł', 'rate' => 4.0, 'locale' => 'pl_PL'],
    'en' => ['code' => 'USD', 'symbol' => '$', 'rate' => 1.0, 'locale' => 'en_US'],
    'de' => ['code' => 'EUR', 'symbol' => '€', 'rate' => 0.92, 'locale' => 'de_DE'],
];
$getCurrencyConfig = fn(): array => $currencyConfig[$lang] ?? $currencyConfig['en'];

// ---- Logger ----
if (is_readable(__DIR__ . '/lib/Logger.php')) {
    require_once __DIR__ . '/lib/Logger.php';
    Logger::setLogDir(__DIR__ . '/var/logs');
    Logger::enableDebug(env('APP_DEBUG') === '1' || env('APP_ENV') === 'dev');
}

function h(string $s): string { return htmlspecialchars($s, ENT_QUOTES | ENT_HTML5, 'UTF-8'); }

function csrf_token(): string {
    if (empty($_SESSION['csrf'])) $_SESSION['csrf'] = bin2hex(random_bytes(16));
    return $_SESSION['csrf'];
}

function check_rate_limit(): bool {
    $now = time();
    $last = $_SESSION['last_submit'] ?? 0;
    if ($now - (int)$last < 60) return false;
    $_SESSION['last_submit'] = $now;
    return true;
}

function send_notification(string $subject, string $body): bool {
    $to = env('CONTACT_EMAIL');
    if ($to === '') return false;
    $from = env('MAIL_FROM', 'no-reply@' . ($_SERVER['HTTP_HOST'] ?? 'localhost'));

    // Check if SMTP is configured
    $smtpHost = env('SMTP_HOST');
    if ($smtpHost !== '') {
        return send_notification_smtp($to, $from, $subject, $body);
    }

    // Fallback to native mail()
    $headers = [
        'From: REDSL Landing <' . $from . '>',
        'Reply-To: ' . $from,
        'Content-Type: text/plain; charset=UTF-8',
        'X-Mailer: PHP/' . phpversion(),
    ];
    return @mail($to, '=?UTF-8?B?' . base64_encode($subject) . '?=', $body, implode("\r\n", $headers));
}

function send_notification_smtp(string $to, string $from, string $subject, string $body): bool {
    // Autoload PHPMailer if available
    $autoload = __DIR__ . '/vendor/autoload.php';
    if (!file_exists($autoload)) {
        error_log('PHPMailer not installed. Run: composer install');
        return false;
    }
    require_once $autoload;

    try {
        $mail = new PHPMailer\PHPMailer\PHPMailer(true);
        $mail->isSMTP();
        $mail->Host = env('SMTP_HOST');
        $mail->Port = (int) env('SMTP_PORT', '587');
        $mail->SMTPAuth = true;
        $mail->Username = env('SMTP_USER');
        $mail->Password = env('SMTP_PASS');
        $mail->SMTPSecure = env('SMTP_ENCRYPTION', 'tls');
        $mail->CharSet = 'UTF-8';

        $mail->setFrom($from, 'REDSL Landing');
        $mail->addAddress($to);
        $mail->addReplyTo($from);
        $mail->Subject = $subject;
        $mail->Body = $body;

        return $mail->send();
    } catch (Exception $e) {
        error_log('SMTP error: ' . $e->getMessage());
        return false;
    }
}

// =============================================================
//  ROUTING
// =============================================================

$action = $_GET['action'] ?? '';
$feedback = null;
$feedbackType = null;
$githubUser = null;

// --- GitHub OAuth: initiate ---
if ($action === 'github-login') {
    $state = bin2hex(random_bytes(12));
    $_SESSION['oauth_state'] = $state;
    $clientId = env('GITHUB_CLIENT_ID');
    $redirect = env('GITHUB_REDIRECT_URI');
    if ($clientId === '' || $redirect === '') {
        if (class_exists('Logger')) {
            Logger::warning('oauth', 'OAuth not configured (missing CLIENT_ID or REDIRECT_URI)', [
                'has_client_id' => $clientId !== '',
                'has_redirect' => $redirect !== '',
            ]);
        }
        header('Location: /?err=oauth_not_configured');
        exit;
    }
    $oauthBase = env('GITHUB_OAUTH_BASE') ?: 'https://github.com';
    $params = http_build_query([
        'client_id'    => $clientId,
        'redirect_uri' => $redirect,
        'scope'        => 'read:user user:email public_repo',
        'state'        => $state,
        'allow_signup' => 'true',
    ]);
    if (class_exists('Logger')) {
        Logger::info('oauth', 'Login initiated', [
            'oauth_base' => $oauthBase,
            'redirect_uri' => $redirect,
            'state' => substr($state, 0, 8) . '...',
            'is_mock' => str_contains($oauthBase, 'localhost'),
        ]);
    }
    header('Location: ' . $oauthBase . '/login/oauth/authorize?' . $params);
    exit;
}

// --- GitHub OAuth: callback ---
if (isset($_GET['code'], $_GET['state'])) {
    $state = $_GET['state'];
    $expected = $_SESSION['oauth_state'] ?? '';
    unset($_SESSION['oauth_state']);

    if (!hash_equals($expected, $state)) {
        if (class_exists('Logger')) {
            Logger::warning('oauth', 'State mismatch (possible CSRF)', [
                'expected_prefix' => substr($expected, 0, 8),
                'got_prefix' => substr($state, 0, 8),
            ]);
        }
        $feedback = 'Nieprawidłowy state — spróbuj ponownie.';
        $feedbackType = 'error';
    } else {
        $code = $_GET['code'];
        // Use API base for server-side calls (internal URL in Docker/mock mode),
        // fall back to OAUTH_BASE (which defaults to github.com for real GitHub)
        $tokenBase = env('GITHUB_API_BASE') ?: env('GITHUB_OAUTH_BASE') ?: 'https://github.com';
        $tokenUrl = $tokenBase . '/login/oauth/access_token';
        
        if (class_exists('Logger')) {
            Logger::info('oauth', 'Exchanging code for token', [
                'token_url' => $tokenUrl,
                'code_prefix' => substr($code, 0, 10),
            ]);
        }
        
        $ch = curl_init($tokenUrl);
        curl_setopt_array($ch, [
            CURLOPT_POST           => true,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER     => ['Accept: application/json', 'User-Agent: redsl-landing'],
            CURLOPT_POSTFIELDS     => http_build_query([
                'client_id'     => env('GITHUB_CLIENT_ID'),
                'client_secret' => env('GITHUB_CLIENT_SECRET'),
                'code'          => $code,
                'redirect_uri'  => env('GITHUB_REDIRECT_URI'),
            ]),
            CURLOPT_TIMEOUT        => 10,
        ]);
        $resp = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curlError = curl_error($ch);
        curl_close($ch);
        $data = json_decode($resp ?: '', true);
        $token = $data['access_token'] ?? null;

        if (!$token) {
            if (class_exists('Logger')) {
                Logger::error('oauth', 'Token exchange failed', [
                    'token_url' => $tokenUrl,
                    'http_code' => $httpCode,
                    'curl_error' => $curlError ?: null,
                    'response_preview' => substr((string)$resp, 0, 300),
                    'response_error' => $data['error'] ?? null,
                    'response_desc' => $data['error_description'] ?? null,
                    'hint' => 'Sprawdź GITHUB_CLIENT_SECRET i czy redirect_uri zgadza się z tym w GitHub OAuth App',
                ]);
            }
            $feedback = 'Nie udało się uzyskać tokenu z GitHub.';
            $feedbackType = 'error';
        } else {
            $apiBase = env('GITHUB_API_BASE') ?: 'https://api.github.com';
            $userUrl = $apiBase . '/user';
            
            $ch = curl_init($userUrl);
            curl_setopt_array($ch, [
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_HTTPHEADER     => [
                    'Authorization: Bearer ' . $token,
                    'Accept: application/json',
                    'User-Agent: redsl-landing',
                ],
                CURLOPT_TIMEOUT => 10,
            ]);
            $userJson = curl_exec($ch);
            $userHttpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            $user = json_decode($userJson ?: '', true);
            $githubUser = $user['login'] ?? null;
            
            if (class_exists('Logger')) {
                Logger::info('oauth', 'User profile fetched', [
                    'user_url' => $userUrl,
                    'http_code' => $userHttpCode,
                    'login' => $githubUser ?: 'NONE',
                ]);
            }

            if ($githubUser) {
                // Store user in session for dashboard access
                $_SESSION['github_user'] = [
                    'login'        => $user['login'] ?? '',
                    'name'         => $user['name'] ?? '',
                    'email'        => $user['email'] ?? '',
                    'company'      => $user['company'] ?? '',
                    'avatar_url'   => $user['avatar_url'] ?? '',
                    'html_url'     => $user['html_url'] ?? 'https://github.com/' . $githubUser,
                    'public_repos' => $user['public_repos'] ?? 0,
                    'logged_at'    => time(),
                ];
                
                if (class_exists('Logger')) {
                    Logger::info('oauth', 'Login successful', [
                        'login' => $githubUser,
                        'email' => $user['email'] ?? null,
                    ]);
                }
                
                // Send notification (non-blocking - don't fail login if it errors)
                @send_notification(
                    "Nowy lead przez GitHub: @$githubUser",
                    "Login: $githubUser\n" .
                    "Name: " . ($user['name'] ?? '-') . "\n" .
                    "Email: " . ($user['email'] ?? '-') . "\n" .
                    "Company: " . ($user['company'] ?? '-') . "\n" .
                    "Public repos: " . ($user['public_repos'] ?? '?') . "\n" .
                    "Profile: https://github.com/$githubUser\n\n" .
                    "Zeskanuj i wyślij raport w ciągu 24h."
                );
                
                // Redirect to client dashboard
                header('Location: /klient/');
                exit;
            } else {
                if (class_exists('Logger')) {
                    Logger::error('oauth', 'Profile fetch returned no login', [
                        'http_code' => $userHttpCode,
                        'response_preview' => substr((string)$userJson, 0, 300),
                    ]);
                }
                $feedback = 'Nie udało się odczytać profilu z GitHub.';
                $feedbackType = 'error';
            }
        }
    }
}

// --- Contact form POST ---
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['form'] ?? '') === 'contact') {
    $token = $_POST['csrf'] ?? '';
    if (!hash_equals(csrf_token(), $token)) {
        $feedback = 'Token formularza wygasł — odśwież stronę.';
        $feedbackType = 'error';
    } elseif (!check_rate_limit()) {
        $feedback = 'Zaczekaj chwilę przed kolejną wiadomością.';
        $feedbackType = 'error';
    } else {
        // Honeypot field — bots fill this, humans don't see it
        if (!empty($_POST['website'])) {
            $feedback = 'Dziękujemy — wiadomość wysłana.'; // silent success for bots
            $feedbackType = 'success';
        } else {
            $name   = trim((string)($_POST['name'] ?? ''));
            $email  = trim((string)($_POST['email'] ?? ''));
            $repo   = trim((string)($_POST['repo'] ?? ''));
            $msg    = trim((string)($_POST['message'] ?? ''));

            $errs = [];
            if ($name === '' || mb_strlen($name) > 120) $errs[] = 'imię';
            if (!filter_var($email, FILTER_VALIDATE_EMAIL)) $errs[] = 'email';
            if (mb_strlen($msg) > 4000) $errs[] = 'wiadomość (za długa)';

            if ($errs) {
                $feedback = 'Sprawdź pola: ' . implode(', ', $errs) . '.';
                $feedbackType = 'error';
            } else {
                $body = "Od: $name <$email>\n" .
                        "Repo: " . ($repo !== '' ? $repo : '-') . "\n" .
                        "Wiadomość:\n$msg\n\n" .
                        "--\nIP: " . ($_SERVER['REMOTE_ADDR'] ?? '-') . "\n" .
                        "UA: " . ($_SERVER['HTTP_USER_AGENT'] ?? '-') . "\n";
                $ok = send_notification("REDSL kontakt: $name", $body);
                if ($ok) {
                    $feedback = 'Dzięki — odpowiemy w ciągu jednego dnia roboczego.';
                    $feedbackType = 'success';
                    unset($_SESSION['csrf']);
                } else {
                    $feedback = 'Coś poszło nie tak z wysyłką. Napisz bezpośrednio: ' . env('CONTACT_EMAIL', 'kontakt@example.com');
                    $feedbackType = 'error';
                }
            }
        }
    }
}

if (isset($_GET['err']) && $_GET['err'] === 'oauth_not_configured') {
    $feedback = $t('errors.oauth_not_configured');
    $feedbackType = 'error';
}

$csrf = csrf_token();
$year = date('Y');
$issue = date('Y.m');
?>
<!DOCTYPE html>
<html lang="<?=h($lang)?>">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="<?=h($t('meta.description'))?>">
<meta name="robots" content="index, follow">
<meta property="og:title" content="<?=h($t('meta.title'))?>">
<meta property="og:description" content="<?=h($t('meta.description'))?>">
<meta property="og:type" content="website">
<title><?=h($t('meta.title'))?></title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&family=Instrument+Sans:ital,wght@0,400..700;1,400..700&family=JetBrains+Mono:wght@400;500;700&display=swap">
<link rel="stylesheet" href="style.css">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23c8442d'/%3E%3Ctext x='50%25' y='58%25' font-family='serif' font-size='22' fill='%23f4efe6' text-anchor='middle' font-weight='900'%3ER%3C/text%3E%3C/svg%3E">
</head>
<body>

<!-- ============ MASTHEAD ============ -->
<header class="masthead">
    <div class="masthead-inner">
        <div class="masthead-left">
            <span class="issue"><?=h($t('meta.issue'))?> <?=h($issue)?></span>
            <span class="dot">·</span>
            <span class="date"><?=h(date('j F Y'))?></span>
        </div>
        <a href="#" class="logo">
            <span class="logo-r">R</span><span>edsl</span>
        </a>
        <nav class="masthead-right">
            <a href="#jak"><?=h($t('nav.how_it_works'))?></a>
            <a href="#cennik"><?=h($t('nav.pricing'))?></a>
            <a href="/config-editor.php"><?=h($t('nav.config'))?></a>
            <a href="/proposals"><?=h($t('nav.proposals'))?></a>
            <a href="#kontakt"><?=h($t('nav.contact'))?></a>
            <!-- Language Switcher -->
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

<!-- ============ HERO ============ -->
<section class="hero">
    <div class="container">
        <div class="kicker"><?=h($t('hero.kicker'))?></div>

        <h1 class="headline">
            <?=h($t('hero.headline'))?>
        </h1>

        <p class="lede">
            <?=h($t('hero.lede'))?>
        </p>

        <ul class="hero-bullets">
            <li>🧠 <?=h($t('hero.bullet1'))?></li>
            <li>⚙️ <?=h($t('hero.bullet2'))?></li>
            <li>📉 <?=h($t('hero.bullet3'))?></li>
        </ul>

        <div class="hero-cta">
            <a href="?action=github-login&lang=<?=h($lang)?>" class="btn btn-primary">
                <?=h($t('hero.cta_scan'))?>
            </a>
            <a href="#jak" class="btn btn-ghost"><?=h($t('hero.cta_how'))?></a>
        </div>

        <div class="hero-meta">
            <span><?=h($t('hero.meta_scan'))?></span>
            <span class="sep">/</span>
            <span><?=h($t('hero.meta_no_sub'))?></span>
            <span class="sep">/</span>
            <span><?=h($t('hero.meta_pay'))?></span>
        </div>
    </div>
</section>

<?php if ($feedback): ?>
<div class="flash flash-<?=h($feedbackType)?>">
    <div class="container"><?=h($feedback)?></div>
</div>
<?php endif; ?>

<!-- ============ BÓL ============ -->
<section class="section pain">
    <div class="container">
        <div class="section-label"><?=h($t('pain.label'))?></div>
        <h2 class="section-title"><?=h($t('pain.title'))?></h2>

        <div class="pain-grid">
            <div class="pain-col pain-before">
                <div class="pain-label"><span class="pain-icon">✗</span> <?=h($t('pain.without'))?></div>
                <ul>
                    <li><?=h($t('pain.without_1'))?></li>
                    <li><?=h($t('pain.without_2'))?></li>
                    <li><?=h($t('pain.without_3'))?></li>
                    <li><?=h($t('pain.without_4'))?></li>
                </ul>
            </div>
            <div class="pain-col pain-after">
                <div class="pain-label"><span class="pain-icon">✓</span> <?=h($t('pain.with'))?></div>
                <ul>
                    <li><?=h($t('pain.with_1'))?></li>
                    <li><?=h($t('pain.with_2'))?></li>
                    <li><?=h($t('pain.with_3'))?></li>
                    <li><?=h($t('pain.with_4'))?></li>
                </ul>
            </div>
        </div>

        <p class="pain-punchline"><?=h($t('pain.punchline'))?></p>
    </div>
</section>

<!-- ============ DLACZEGO ============ -->
<section class="section why">
    <div class="container">
        <div class="section-label"><?=h($t('why.label'))?></div>
        <div class="why-grid">
            <div>
                <h3><?=h($t('why.title_1'))?></h3>
                <p><?=h($t('why.desc_1'))?></p>
            </div>
            <div>
                <h3><?=h($t('why.title_2'))?></h3>
                <p><?=h($t('why.desc_2'))?></p>
            </div>
            <div>
                <h3><?=h($t('why.title_3'))?></h3>
                <p><?=h($t('why.desc_3'))?></p>
            </div>
        </div>
    </div>
</section>

<!-- ============ JAK DZIAŁA ============ -->
<section class="section process" id="jak">
    <div class="container">
        <div class="section-label"><?=h($t('process.label'))?></div>
        <h2 class="section-title"><?=h($t('process.title'))?></h2>

        <ol class="steps">
            <li>
                <div class="step-num">I</div>
                <div class="step-body">
                    <h4><?=$th('process.step1_title')?></h4>
                    <p><?=$th('process.step1_desc')?></p>
                </div>
            </li>
            <li>
                <div class="step-num">II</div>
                <div class="step-body">
                    <h4><?=$th('process.step2_title')?></h4>
                    <p><?=$th('process.step2_desc')?></p>
                </div>
            </li>
            <li>
                <div class="step-num">III</div>
                <div class="step-body">
                    <h4><?=$th('process.step3_title')?></h4>
                    <p><?=$th('process.step3_desc', [h($formatPrice(50.0))])?></p>
                </div>
            </li>
            <li>
                <div class="step-num">IV</div>
                <div class="step-body">
                    <h4><?=$th('process.step4_title')?></h4>
                    <p><?=$th('process.step4_desc')?></p>
                </div>
            </li>
            <li>
                <div class="step-num">V</div>
                <div class="step-body">
                    <h4><?=$th('process.step5_title')?></h4>
                    <p><?=$th('process.step5_desc')?></p>
                </div>
            </li>
        </ol>
    </div>
</section>

<!-- ============ CENNIK ============ -->
<section class="section pricing" id="cennik">
    <div class="container">
        <div class="section-label"><?=h($t('pricing.label'))?></div>
        <h2 class="section-title"><?=h($t('pricing.title'))?></h2>

        <div class="price-grid">
            <!-- Ticket znaleziony -->
            <article class="price-card">
                <div class="price-tag">
                    <span class="tag-corner tag-corner-tl"></span>
                    <span class="tag-corner tag-corner-tr"></span>
                    <span class="tag-corner tag-corner-bl"></span>
                    <span class="tag-corner tag-corner-br"></span>
                    <div class="price-label"><?=h($t('pricing.found_title'))?></div>
                    <div class="price-value">
                        <span class="amount"><?=h($getPricing('ticket_found', false))?></span>
                        <span class="currency"><?=h($getCurrencyConfig()['symbol'])?></span>
                    </div>
                </div>
                <div class="price-desc">
                    <p class="price-what"><?=h($t('pricing.found_desc'))?></p>
                    <ul class="price-list">
                        <li><strong><?=h($t('pricing.found_scope'))?></strong> — <?=h($t('pricing.found_scope_desc'))?></li>
                        <li><strong><?=h($t('pricing.found_merge'))?></strong> — <?=h($t('pricing.found_merge_desc'))?></li>
                        <li><strong><?=h($t('pricing.found_guarantee'))?></strong> — <?=h($t('pricing.found_guarantee_desc'))?></li>
                    </ul>
                </div>
            </article>

            <!-- Ticket klienta -->
            <article class="price-card">
                <div class="price-tag price-tag-alt">
                    <span class="tag-corner tag-corner-tl"></span>
                    <span class="tag-corner tag-corner-tr"></span>
                    <span class="tag-corner tag-corner-bl"></span>
                    <span class="tag-corner tag-corner-br"></span>
                    <div class="price-label"><?=h($t('pricing.made_title'))?></div>
                    <div class="price-value">
                        <span class="amount"><?=h($getPricing('ticket_found', false))?></span>
                        <span class="currency"><?=h($getCurrencyConfig()['symbol'])?></span>
                    </div>
                </div>
                <div class="price-desc">
                    <p class="price-what"><?=h($t('pricing.made_desc'))?></p>
                    <ul class="price-list">
                        <li><strong><?=h($t('pricing.made_report'))?></strong> — <?=h($t('pricing.made_report_desc'))?></li>
                        <li><strong><?=h($t('pricing.made_quote'))?></strong> — <?=h($t('pricing.made_quote_desc'))?></li>
                        <li><strong><?=h($t('pricing.made_delivery'))?></strong> — <?=h($t('pricing.made_delivery_desc'))?></li>
                    </ul>
                </div>
            </article>
        </div>

        <div class="bulk-note">
            <strong><?=h($t('pricing.bundle_title'))?></strong>
            — <?=h(sprintf($t('pricing.bundle_note'), h($getPricing('bundle_20'))))?>
        </div>
    </div>
</section>

<!-- ============ SCOPE ============ -->
<section class="section scope">
    <div class="container">
        <div class="section-label"><?=h($t('scope.label'))?></div>
        <div class="scope-grid">
            <div class="scope-col">
                <h3 class="scope-title scope-yes"><?=h($t('scope.yes_title'))?></h3>
                <ul>
                    <li><?=h($t('scope.yes_1'))?></li>
                    <li><?=h($t('scope.yes_2'))?></li>
                    <li><?=h($t('scope.yes_3'))?></li>
                    <li><?=h($t('scope.yes_4'))?></li>
                    <li><?=h($t('scope.yes_5'))?></li>
                    <li><?=h($t('scope.yes_6'))?></li>
                </ul>
            </div>
            <div class="scope-col">
                <h3 class="scope-title scope-no"><?=h($t('scope.no_title'))?></h3>
                <ul>
                    <li><?=h($t('scope.no_1'))?></li>
                    <li><?=h($t('scope.no_2'))?></li>
                    <li><?=h($t('scope.no_3'))?></li>
                    <li><?=$th('scope.no_4')?></li>
                </ul>
            </div>
        </div>
    </div>
</section>

<!-- ============ BEZPIECZEŃSTWO ============ -->
<section class="section security">
    <div class="container">
        <div class="section-label"><?=h($t('security.label'))?></div>
        <div class="security-grid">
            <div><strong><a href="/nda-form" style="color: inherit; text-decoration: underline;"><?=h($t('security.nda'))?></a></strong><span><?=h($t('security.nda_desc'))?></span></div>
            <div><strong><?=h($t('security.access'))?></strong><span><?=h($t('security.access_desc'))?></span></div>
            <div><strong><?=h($t('security.retention'))?></strong><span><?=h($t('security.retention_desc'))?></span></div>
            <div><strong><?=h($t('security.secrets'))?></strong><span><?=h($t('security.secrets_desc'))?></span></div>
            <div><strong><?=h($t('security.jurisdiction'))?></strong><span><?=h($t('security.jurisdiction_desc'))?></span></div>
            <div><strong><?=h($t('security.audit'))?></strong><span><?=h($t('security.audit_desc'))?></span></div>
        </div>
    </div>
</section>

<!-- ============ FAQ ============ -->
<section class="section faq">
    <div class="container">
        <div class="section-label"><?=h($t('faq.label'))?></div>

        <details class="q">
            <summary><?=h($t('faq.q1_summary'))?></summary>
            <p><?=h($t('faq.q1_text'))?></p>
        </details>

        <details class="q">
            <summary><?=h($t('faq.q2_summary'))?></summary>
            <p><?=h($t('faq.q2_text'))?></p>
        </details>

        <details class="q">
            <summary><?=h($t('faq.q3_summary'))?></summary>
            <p><?=$th('faq.q3_text')?></p>
        </details>

        <details class="q">
            <summary><?=h($t('faq.q4_summary'))?></summary>
            <p><?=h($t('faq.q4_text'))?></p>
        </details>

        <details class="q">
            <summary><?=h($t('faq.q5_summary'))?></summary>
            <p><?=h($t('faq.q5_text'))?></p>
        </details>
    </div>
</section>

<!-- ============ KONTAKT ============ -->
<section class="section contact" id="kontakt">
    <div class="container contact-container">
        <div class="contact-left">
            <div class="section-label"><?=h($t('contact.label'))?></div>
            <h2 class="section-title"><?=$th('contact.title')?></h2>
            <p class="contact-lede"><?=h($t('contact.lede'))?></p>

            <div class="contact-github">
                <a href="?action=github-login" class="btn btn-primary btn-block">
                    <svg viewBox="0 0 16 16" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
                    <?=h($t('contact.github_btn'))?>
                </a>
                <p class="contact-micro"><?=h($t('contact.github_micro'))?></p>
            </div>

            <div class="contact-divider"><span><?=h($t('contact.or'))?></span></div>

            <form method="post" action="?#kontakt" class="contact-form" novalidate>
                <input type="hidden" name="form" value="contact">
                <input type="hidden" name="csrf" value="<?=h($csrf)?>">
                <input type="text" name="website" class="honeypot" tabindex="-1" autocomplete="off" aria-hidden="true">

                <label>
                    <span><?=h($t('contact.form_name'))?></span>
                    <input type="text" name="name" required maxlength="120" autocomplete="name">
                </label>
                <label>
                    <span><?=h($t('contact.form_email'))?></span>
                    <input type="email" name="email" required maxlength="200" autocomplete="email">
                </label>
                <label>
                    <span><?=$th('contact.form_repo')?></span>
                    <input type="url" name="repo" maxlength="300" placeholder="https://github.com/twoja-firma/twoj-projekt">
                </label>
                <label>
                    <span><?=$th('contact.form_message')?></span>
                    <textarea name="message" rows="3" maxlength="4000" placeholder="<?=h($t('contact.form_placeholder'))?>"></textarea>
                </label>
                <button type="submit" class="btn btn-primary btn-block"><?=h($t('contact.form_submit'))?></button>
                <p class="contact-micro"><?=h($t('contact.form_micro'))?></p>
            </form>
        </div>

        <aside class="contact-right">
            <div class="sidebar-block">
                <h4><?=h($t('contact.sidebar_for'))?></h4>
                <p><?=$th('contact.sidebar_for_desc')?></p>
            </div>
            <div class="sidebar-block">
                <h4><?=h($t('contact.sidebar_not'))?></h4>
                <p><?=h($t('contact.sidebar_not_desc'))?></p>
            </div>
            <div class="sidebar-block sidebar-quote">
                <p>„<?=$th('contact.sidebar_quote')?>”</p>
            </div>
        </aside>
    </div>
</section>

<!-- ============ FOOTER / KOLOFON ============ -->
<footer class="colophon">
    <div class="container">
        <div class="colophon-grid">
            <div>
                <div class="footer-logo"><span class="logo-r">R</span>edsl</div>
                <p class="footer-sub"><?=h($t('footer.tagline'))?></p>
            </div>
            <div>
                <h5><?=h($t('footer.product'))?></h5>
                <ul>
                    <li><a href="#jak"><?=h($t('nav.how_it_works'))?></a></li>
                    <li><a href="#cennik"><?=h($t('nav.pricing'))?></a></li>
                    <li><a href="#kontakt"><?=h($t('nav.contact'))?></a></li>
                </ul>
            </div>
            <div>
                <h5><?=h($t('footer.resources'))?></h5>
                <ul>
                    <li><a href="https://github.com/wronai/redsl" rel="noopener">GitHub</a></li>
                    <li><a href="https://github.com/wronai/redsl/tree/main/docs" rel="noopener">Docs</a></li>
                    <li><a href="/blog/">Blog</a></li>
                </ul>
            </div>
            <div>
                <h5><?=h($t('footer.legal'))?></h5>
                <ul>
                    <li><a href="/nda-wzor"><?=h($t('footer.nda'))?></a></li>
                    <li><a href="/polityka-prywatnosci"><?=h($t('footer.privacy'))?></a></li>
                    <li><a href="/regulamin"><?=h($t('footer.terms'))?></a></li>
                </ul>
            </div>
        </div>
        <div class="colophon-bottom">
            <span>&copy; <?=h((string)$year)?> REDSL &middot; <?=h($t('meta.issue'))?> <?=h($issue)?></span>
            <span class="dot">&middot;</span>
            <span>Polska &middot; UE</span>
            <span class="dot">&middot;</span>
            <span><?=h($t('footer.copyright'))?></span>
    </div>
</footer>

<script src="app.js" defer></script>
</body>
</html>
