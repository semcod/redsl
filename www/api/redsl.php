<?php
declare(strict_types=1);

/**
 * ReDSL API proxy
 *
 * Forwards requests from the www frontend to the redsl-api service.
 * Endpoints:
 *   GET  /api/redsl.php?action=health
 *   POST /api/redsl.php?action=scan      body: {"project": "goal"}
 *   POST /api/redsl.php?action=refactor  body: {"project": "goal", "dry_run": true, "max_actions": 5}
 *   POST /api/redsl.php?action=analyze   body: {"project": "goal"}
 */

// ── Config ───────────────────────────────────────────────────────
$REDSL_API = getenv('REDSL_API_URL') ?: 'http://redsl-api:8000';
$WORKSPACE = getenv('WORKSPACE_ROOT') ?: '/workspace';
$API_SECRET = getenv('REDSL_API_SECRET') ?: '';

header('Content-Type: application/json; charset=UTF-8');
header('X-Content-Type-Options: nosniff');

// ── Auth (optional shared secret) ────────────────────────────────
if ($API_SECRET !== '') {
    $given = $_SERVER['HTTP_X_REDSL_SECRET'] ?? '';
    if (!hash_equals($API_SECRET, $given)) {
        http_response_code(401);
        echo json_encode(['error' => 'Unauthorized']);
        exit;
    }
}

// ── Helpers ───────────────────────────────────────────────────────
function redsl_curl(string $method, string $url, ?array $body = null): array {
    $ch = curl_init($url);
    $opts = [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 120,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json', 'Accept: application/json'],
    ];
    if ($method === 'POST') {
        $opts[CURLOPT_POST]       = true;
        $opts[CURLOPT_POSTFIELDS] = $body !== null ? json_encode($body) : '{}';
    }
    curl_setopt_array($ch, $opts);
    $resp     = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err      = curl_error($ch);
    curl_close($ch);

    if ($err) {
        return ['ok' => false, 'code' => 0, 'body' => null, 'error' => $err];
    }
    $decoded = json_decode($resp ?: '{}', true);
    return ['ok' => $httpCode >= 200 && $httpCode < 300, 'code' => $httpCode, 'body' => $decoded, 'error' => null];
}

function json_out(int $code, mixed $data): never {
    http_response_code($code);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

function resolve_project(string $name): string|false {
    global $WORKSPACE;
    $clean = preg_replace('/[^a-zA-Z0-9_\-]/', '', $name);
    if ($clean === '') return false;
    $path = $WORKSPACE . '/' . $clean;
    return $path;
}

// ── Router ────────────────────────────────────────────────────────
$action = $_GET['action'] ?? '';
$rawBody = file_get_contents('php://input');
$body = json_decode($rawBody ?: '{}', true) ?? [];

// ── GET /api/redsl.php?action=health ─────────────────────────────
if ($action === 'health') {
    $r = redsl_curl('GET', "$REDSL_API/health");
    if (!$r['ok']) {
        json_out(502, ['status' => 'redsl-api unreachable', 'error' => $r['error']]);
    }
    json_out(200, array_merge(['status' => 'ok'], $r['body'] ?? []));
}

// ── POST /api/redsl.php?action=scan ──────────────────────────────
if ($action === 'scan' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $project = (string)($body['project'] ?? '');
    if ($project === '') {
        json_out(400, ['error' => 'Missing: project']);
    }
    $projectPath = resolve_project($project);
    if ($projectPath === false) {
        json_out(400, ['error' => 'Invalid project name']);
    }
    $r = redsl_curl('POST', "$REDSL_API/analyze", ['project_dir' => $projectPath]);
    json_out($r['ok'] ? 200 : 502, $r['body'] ?? ['error' => $r['error']]);
}

// ── POST /api/redsl.php?action=refactor ──────────────────────────
if ($action === 'refactor' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $project    = (string)($body['project'] ?? '');
    $dryRun     = (bool)($body['dry_run'] ?? true);
    $maxActions = min((int)($body['max_actions'] ?? 5), 20);

    if ($project === '') {
        json_out(400, ['error' => 'Missing: project']);
    }
    $projectPath = resolve_project($project);
    if ($projectPath === false) {
        json_out(400, ['error' => 'Invalid project name']);
    }

    $payload = [
        'project_dir' => $projectPath,
        'dry_run'     => $dryRun,
        'max_actions' => $maxActions,
    ];
    $r = redsl_curl('POST', "$REDSL_API/refactor", $payload);
    json_out($r['ok'] ? 200 : 502, $r['body'] ?? ['error' => $r['error']]);
}

// ── POST /api/redsl.php?action=batch ─────────────────────────────
if ($action === 'batch' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $maxActions = min((int)($body['max_actions'] ?? 5), 20);
    $r = redsl_curl('POST', "$REDSL_API/batch/semcod", [
        'semcod_root'  => $WORKSPACE,
        'max_actions'  => $maxActions,
    ]);
    json_out($r['ok'] ? 200 : 502, $r['body'] ?? ['error' => $r['error']]);
}

// ── Fallback ──────────────────────────────────────────────────────
json_out(400, [
    'error'   => 'Unknown action',
    'actions' => ['health', 'scan', 'refactor', 'batch'],
]);
