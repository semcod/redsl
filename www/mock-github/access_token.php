<?php
/**
 * Mock GitHub OAuth - Access Token endpoint
 * 
 * Simulates: POST https://github.com/login/oauth/access_token
 * 
 * Exchanges authorization code for access token.
 */

declare(strict_types=1);

// We need access to the session where authorize.php stored the code
// Client connects with its own session ID from cookie or different flow
// For mock purposes, we use a shared file store

$storeFile = sys_get_temp_dir() . '/mock-github-codes.json';

// Accept both POST body and form
$input = $_POST;
if (empty($input)) {
    $raw = file_get_contents('php://input');
    $input = [];
    parse_str($raw, $input);
    
    // Also try JSON
    if (empty($input)) {
        $json = json_decode($raw, true);
        if (is_array($json)) $input = $json;
    }
}

$clientId = $input['client_id'] ?? '';
$clientSecret = $input['client_secret'] ?? '';
$code = $input['code'] ?? '';

header('Content-Type: application/json');

if (!$code) {
    http_response_code(400);
    echo json_encode(['error' => 'bad_verification_code', 'error_description' => 'Missing code']);
    exit;
}

// Load codes from shared store
$codes = [];
if (file_exists($storeFile)) {
    $contents = file_get_contents($storeFile);
    $codes = json_decode($contents, true) ?: [];
}

if (!isset($codes[$code])) {
    http_response_code(401);
    echo json_encode(['error' => 'bad_verification_code', 'error_description' => 'Code not found or expired']);
    exit;
}

$userData = $codes[$code];

// Check expiry (10 min)
if (time() - ($userData['issued_at'] ?? 0) > 600) {
    unset($codes[$code]);
    file_put_contents($storeFile, json_encode($codes));
    http_response_code(401);
    echo json_encode(['error' => 'expired_token', 'error_description' => 'Code expired']);
    exit;
}

// Generate token
$token = 'mock_ghp_' . bin2hex(random_bytes(20));

// Store user data for /user endpoint (by token now)
$userData['token'] = $token;
$codes['token:' . $token] = $userData;
unset($codes[$code]); // one-time use

file_put_contents($storeFile, json_encode($codes));

echo json_encode([
    'access_token' => $token,
    'token_type' => 'bearer',
    'scope' => 'read:user,user:email,public_repo',
]);
