<?php
/**
 * Mock GitHub OAuth - Authorize endpoint
 * 
 * Simulates: https://github.com/login/oauth/authorize
 * 
 * Shows a "fake consent screen" and redirects to client's redirect_uri
 * with a synthetic authorization code.
 */

declare(strict_types=1);

$storeFile = sys_get_temp_dir() . '/mock-github-codes.json';

$clientId = $_GET['client_id'] ?? '';
$redirectUri = $_GET['redirect_uri'] ?? '';
$scope = $_GET['scope'] ?? '';
$state = $_GET['state'] ?? '';

if (!$clientId || !$redirectUri) {
    http_response_code(400);
    echo "Missing client_id or redirect_uri";
    exit;
}

// Handle approval
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['approve'] ?? '') === '1') {
    $username = trim($_POST['username'] ?? 'testuser');
    
    // Generate fake auth code
    $code = 'mock_code_' . bin2hex(random_bytes(16));
    
    // Load existing store
    $codes = [];
    if (file_exists($storeFile)) {
        $codes = json_decode(file_get_contents($storeFile), true) ?: [];
    }
    
    // Clean up old codes (> 10 min)
    foreach ($codes as $k => $v) {
        if (isset($v['issued_at']) && time() - $v['issued_at'] > 600) {
            unset($codes[$k]);
        }
    }
    
    // Store user data keyed by code
    $codes[$code] = [
        'username' => $username,
        'name' => $_POST['name'] ?? ucfirst($username) . ' Example',
        'email' => $_POST['email'] ?? $username . '@example.com',
        'company' => $_POST['company'] ?? 'Example Sp. z o.o.',
        'public_repos' => (int)($_POST['public_repos'] ?? 5),
        'issued_at' => time(),
    ];
    
    file_put_contents($storeFile, json_encode($codes));
    
    // Redirect back with code + state
    $sep = str_contains($redirectUri, '?') ? '&' : '?';
    $url = $redirectUri . $sep . http_build_query([
        'code' => $code,
        'state' => $state,
    ]);
    
    header('Location: ' . $url);
    exit;
}

// Show consent screen
?>
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Mock GitHub OAuth — Authorize</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #0d1117; color: #e6edf3; margin: 0; padding: 40px; }
        .container { max-width: 500px; margin: 0 auto; background: #161b22; padding: 40px; border-radius: 8px; border: 1px solid #30363d; }
        h1 { font-size: 20px; margin: 0 0 8px 0; }
        .subtitle { color: #8b949e; margin-bottom: 24px; }
        .warning { background: #1f2428; border-left: 3px solid #f85149; padding: 12px 16px; margin-bottom: 24px; color: #ffa198; font-size: 13px; }
        .app-info { background: #1c2128; padding: 16px; border-radius: 6px; margin-bottom: 24px; font-size: 13px; }
        .app-info strong { color: #58a6ff; }
        label { display: block; margin-bottom: 16px; }
        label span { display: block; font-size: 13px; color: #8b949e; margin-bottom: 4px; }
        input[type="text"], input[type="email"], input[type="number"] {
            width: 100%; box-sizing: border-box; padding: 8px 12px;
            background: #0d1117; border: 1px solid #30363d; border-radius: 6px;
            color: #e6edf3; font-size: 14px;
        }
        input:focus { outline: none; border-color: #58a6ff; }
        .btn-group { display: flex; gap: 8px; margin-top: 24px; }
        button {
            flex: 1; padding: 10px 16px; border-radius: 6px; border: 1px solid #30363d;
            font-size: 14px; font-weight: 500; cursor: pointer;
        }
        .btn-primary { background: #238636; color: white; border-color: #2ea043; }
        .btn-primary:hover { background: #2ea043; }
        .btn-secondary { background: #21262d; color: #e6edf3; }
        .scope { display: flex; align-items: center; gap: 8px; padding: 8px 0; font-size: 13px; }
        .scope-icon { color: #3fb950; }
    </style>
</head>
<body>
    <div class="container">
        <div class="warning">
            🧪 <strong>MOCK GITHUB OAUTH</strong> — To jest symulator tylko do testów lokalnych.
            Nie łączy się z prawdziwym GitHub.
        </div>
        
        <h1>Authorize application</h1>
        <p class="subtitle">Wybierz jakiego użytkownika symulować i kliknij Authorize.</p>
        
        <div class="app-info">
            <div><strong>Client ID:</strong> <?= htmlspecialchars($clientId) ?></div>
            <div><strong>Redirect:</strong> <?= htmlspecialchars($redirectUri) ?></div>
            <div><strong>Scopes:</strong> <?= htmlspecialchars($scope) ?></div>
        </div>
        
        <form method="POST">
            <label>
                <span>GitHub Username</span>
                <input type="text" name="username" value="testuser" required pattern="[a-zA-Z0-9-]+">
            </label>
            <label>
                <span>Full Name</span>
                <input type="text" name="name" value="Test User">
            </label>
            <label>
                <span>Email</span>
                <input type="email" name="email" value="testuser@example.com">
            </label>
            <label>
                <span>Company</span>
                <input type="text" name="company" value="Example Sp. z o.o.">
            </label>
            <label>
                <span>Public Repos Count</span>
                <input type="number" name="public_repos" value="5" min="0" max="999">
            </label>
            
            <div style="margin: 16px 0; padding: 12px; background: #1c2128; border-radius: 6px;">
                <strong style="font-size: 13px;">Requested scopes:</strong>
                <?php foreach (explode(' ', $scope) as $s): if (!$s) continue; ?>
                <div class="scope"><span class="scope-icon">✓</span> <?= htmlspecialchars($s) ?></div>
                <?php endforeach; ?>
            </div>
            
            <div class="btn-group">
                <button type="button" class="btn-secondary" onclick="history.back()">Cancel</button>
                <button type="submit" name="approve" value="1" class="btn-primary">Authorize</button>
            </div>
        </form>
    </div>
</body>
</html>
