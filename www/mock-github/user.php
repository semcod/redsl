<?php
/**
 * Mock GitHub API - User endpoint
 * 
 * Simulates: GET https://api.github.com/user
 * 
 * Returns user profile for the authenticated token.
 */

declare(strict_types=1);

header('Content-Type: application/json');

$storeFile = sys_get_temp_dir() . '/mock-github-codes.json';

// Extract bearer token
$authHeader = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
if (empty($authHeader) && function_exists('getallheaders')) {
    $headers = getallheaders();
    $authHeader = $headers['Authorization'] ?? $headers['authorization'] ?? '';
}

if (!preg_match('/Bearer\s+(\S+)/i', $authHeader, $matches) && !preg_match('/token\s+(\S+)/i', $authHeader, $matches)) {
    http_response_code(401);
    echo json_encode(['message' => 'Bad credentials', 'documentation_url' => 'https://docs.github.com']);
    exit;
}

$token = $matches[1];

// Load user data
$codes = [];
if (file_exists($storeFile)) {
    $codes = json_decode(file_get_contents($storeFile), true) ?: [];
}

if (!isset($codes['token:' . $token])) {
    http_response_code(401);
    echo json_encode(['message' => 'Bad credentials']);
    exit;
}

$u = $codes['token:' . $token];

// Return GitHub-compatible user object
echo json_encode([
    'login' => $u['username'],
    'id' => crc32($u['username']),
    'node_id' => 'MDQ6VXNlcg==',
    'avatar_url' => 'https://via.placeholder.com/96/0d1117/58a6ff?text=' . strtoupper($u['username'][0] ?? 'U'),
    'gravatar_id' => '',
    'url' => 'https://api.github.com/users/' . $u['username'],
    'html_url' => 'https://github.com/' . $u['username'],
    'type' => 'User',
    'name' => $u['name'] ?? null,
    'company' => $u['company'] ?? null,
    'blog' => '',
    'location' => 'Poland',
    'email' => $u['email'] ?? null,
    'hireable' => null,
    'bio' => 'Mock user for testing',
    'public_repos' => $u['public_repos'] ?? 0,
    'public_gists' => 0,
    'followers' => 0,
    'following' => 0,
    'created_at' => date('c', time() - 86400 * 365),
    'updated_at' => date('c'),
]);
