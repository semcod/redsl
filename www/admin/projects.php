<?php
declare(strict_types=1);

require __DIR__ . '/auth.php';
require __DIR__ . '/../lib/Database.php';
require __DIR__ . '/../lib/Repository/ClientRepository.php';
require __DIR__ . '/../lib/Repository/ProjectRepository.php';
require __DIR__ . '/../lib/Service/GithubClient.php';
require __DIR__ . '/../lib/Encryption.php';

$db = Database::connection();
$clientRepo = new ClientRepository($db);
$projectRepo = new ProjectRepository($db);

$action = $_GET['action'] ?? 'list';
$clientId = (int)($_GET['client_id'] ?? 0);
$error = '';
$success = '';

// Handle POST actions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    validateCsrfToken();
    
    $id = (int)($_POST['id'] ?? 0);
    
    if ($action === 'save') {
        $data = [
            'client_id' => (int)($_POST['client_id'] ?? 0),
            'name' => trim($_POST['name'] ?? ''),
            'repo_url' => trim($_POST['repo_url'] ?? ''),
            'repo_provider' => $_POST['repo_provider'] ?? 'github',
            'default_branch' => trim($_POST['default_branch'] ?? 'main'),
            'clone_path' => '', // Will be auto-generated
            'language_primary' => trim($_POST['language_primary'] ?? ''),
            'scan_schedule' => $_POST['scan_schedule'] ?? 'weekly',
            'status' => $_POST['status'] ?? 'active',
        ];
        
        if ($data['client_id'] <= 0) {
            $error = 'Wybierz klienta';
        } elseif (empty($data['name'])) {
            $error = 'Nazwa projektu jest wymagana';
        } elseif (empty($data['repo_url'])) {
            $error = 'URL repozytorium jest wymagany';
        } else {
            try {
                // Generate clone path
                $client = $clientRepo->find($data['client_id']);
                $clientSlug = preg_replace('/[^a-z0-9]+/', '-', strtolower($client['company_name'] ?? 'client'));
                $projectSlug = preg_replace('/[^a-z0-9]+/', '-', strtolower($data['name']));
                $data['clone_path'] = sprintf('var/repos/%s/%s-%s', date('Y'), $clientSlug, $projectSlug);
                
                // Handle token encryption
                $token = trim($_POST['auth_token'] ?? '');
                if (!empty($token)) {
                    if (!Encryption::isConfigured()) {
                        throw new RuntimeException('ENCRYPTION_KEY nie skonfigurowany w .env');
                    }
                    [$cipher, $nonce] = Encryption::encrypt($token);
                    $data['auth_token_encrypted'] = $cipher;
                    $data['auth_token_nonce'] = $nonce;
                }
                
                if ($id > 0) {
                    // Update - don't overwrite token if empty
                    if (empty($token)) {
                        unset($data['auth_token_encrypted'], $data['auth_token_nonce']);
                    }
                    $projectRepo->update($id, $data);
                    $success = 'Projekt zaktualizowany';
                } else {
                    $id = $projectRepo->create($data);
                    $success = 'Projekt utworzony (ID: ' . $id . ')';
                }
                
                header('Location: projects.php?success=' . urlencode($success));
                exit;
            } catch (Throwable $e) {
                $error = 'Błąd: ' . $e->getMessage();
            }
        }
    } elseif ($action === 'delete' && $id > 0) {
        try {
            $projectRepo->update($id, ['status' => 'paused']);
            $success = 'Projekt wstrzymany';
            header('Location: projects.php?success=' . urlencode($success));
            exit;
        } catch (Throwable $e) {
            $error = 'Błąd: ' . $e->getMessage();
        }
    } elseif ($action === 'scan_now' && $id > 0) {
        // Trigger immediate scan by setting next_scan_at to now
        try {
            $projectRepo->update($id, ['next_scan_at' => date('Y-m-d H:i:s'), 'status' => 'active']);
            $success = 'Skan zaplanowany (zostanie wykonany przez cron w ciągu 10 minut)';
            header('Location: projects.php?success=' . urlencode($success));
            exit;
        } catch (Throwable $e) {
            $error = 'Błąd: ' . $e->getMessage();
        }
    }
}

// Show success from redirect
if (isset($_GET['success'])) {
    $success = $_GET['success'];
}

// Get project for edit/view
$project = null;
if (($action === 'edit' || $action === 'view') && isset($_GET['id'])) {
    $project = $projectRepo->find((int)$_GET['id']);
}

// Get client if filtering by client
$client = null;
if ($clientId > 0) {
    $client = $clientRepo->find($clientId);
}

// List projects
$statusFilter = $_GET['status'] ?? null;
if ($clientId > 0) {
    $projects = $projectRepo->findByClient($clientId);
} else {
    $projects = $projectRepo->list($statusFilter, 100);
}

$providers = ['github' => 'GitHub', 'gitlab' => 'GitLab', 'gitea' => 'Gitea', 'bitbucket' => 'Bitbucket'];
$schedules = ['on_demand' => 'Na żądanie', 'daily' => 'Codziennie', 'weekly' => 'Tygodniowo', 'monthly' => 'Miesięcznie'];
$statuses = ['active' => 'Aktywny', 'paused' => 'Wstrzymany', 'error' => 'Błąd'];

// Get all clients for dropdown
$allClients = $clientRepo->list(limit: 1000);
?>
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Projekty — REDSL Panel</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #1a1a2e; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .header h1 { margin: 0; font-size: 24px; }
        .header .nav { margin-top: 10px; }
        .header .nav a { color: #64b5f6; text-decoration: none; margin-right: 20px; }
        .header .nav a:hover { text-decoration: underline; }
        
        .alert { padding: 15px; border-radius: 4px; margin-bottom: 20px; }
        .alert.error { background: #ffebee; color: #c62828; border-left: 4px solid #c62828; }
        .alert.success { background: #e8f5e9; color: #2e7d32; border-left: 4px solid #2e7d32; }
        .alert.info { background: #e3f2fd; color: #1565c0; border-left: 4px solid #1565c0; }
        
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        
        .toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
        .btn { display: inline-block; padding: 10px 20px; background: #1a1a2e; color: white; text-decoration: none; border-radius: 4px; font-size: 14px; border: none; cursor: pointer; }
        .btn:hover { background: #2a2a4e; }
        .btn.secondary { background: #666; }
        .btn.danger { background: #c62828; }
        .btn.success { background: #2e7d32; }
        .btn.small { padding: 5px 10px; font-size: 12px; }
        
        input, select, textarea { padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
        input:focus, select:focus, textarea:focus { outline: none; border-color: #1a1a2e; }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase; background: #fafafa; }
        tr:hover { background: #f9f9f9; }
        
        .badge { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
        .badge.active { background: #e8f5e9; color: #2e7d32; }
        .badge.paused { background: #fff3e0; color: #e65100; }
        .badge.error { background: #ffebee; color: #c62828; }
        
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; font-weight: 500; margin-bottom: 5px; font-size: 14px; }
        .form-group input, .form-group select { width: 100%; }
        .form-group .hint { font-size: 12px; color: #666; margin-top: 4px; }
        
        .project-detail h2 { margin-top: 0; }
        .detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 20px 0; }
        .detail-item dt { font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase; }
        .detail-item dd { margin: 5px 0 0 0; font-size: 16px; }
        .detail-item dd code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-size: 14px; }
        .actions-bar { display: flex; gap: 10px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; flex-wrap: wrap; }
        
        .scan-info { background: #f5f5f5; padding: 15px; border-radius: 4px; margin: 10px 0; }
        .scan-info .label { color: #666; font-size: 12px; }
        .scan-info .value { font-weight: 500; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>REDSL Panel — Projekty</h1>
            <div class="nav">
                <a href="index.php">Dashboard</a>
                <a href="clients.php">Klienci</a>
                <a href="contracts.php">Umowy</a>
                <a href="projects.php">Projekty</a>
                <a href="scans.php">Skany</a>
                <a href="invoices.php">Faktury</a>
            </div>
        </div>
        
        <?php if ($error): ?>
            <div class="alert error"><?= htmlspecialchars($error) ?></div>
        <?php endif; ?>
        <?php if ($success): ?>
            <div class="alert success"><?= htmlspecialchars($success) ?></div>
        <?php endif; ?>
        
        <?php if ($client): ?>
            <div class="alert info">
                <strong>Klient:</strong> <?= htmlspecialchars($client['company_name']) ?> 
                (<a href="clients.php?action=view&id=<?= $client['id'] ?>">zobacz</a>)
            </div>
        <?php endif; ?>
        
        <?php if ($action === 'new' || $action === 'edit'): ?>
            <!-- Form -->
            <div class="card">
                <h2><?= $action === 'edit' ? 'Edytuj projekt' : 'Nowy projekt' ?></h2>
                <form method="POST" action="projects.php?action=save<?= $clientId ? '&client_id=' . $clientId : '' ?>">
                    <input type="hidden" name="csrf_token" value="<?= $_SESSION['csrf_token'] ?>">
                    <?php if ($project): ?>
                        <input type="hidden" name="id" value="<?= $project['id'] ?>">
                    <?php endif; ?>
                    
                    <div class="form-grid">
                        <div class="form-group">
                            <label for="client_id">Klient *</label>
                            <select id="client_id" name="client_id" required <?= $clientId ? 'disabled' : '' ?>>
                                <option value="">-- Wybierz klienta --</option>
                                <?php foreach ($allClients as $c): ?>
                                <option value="<?= $c['id'] ?>" <?= (($project['client_id'] ?? $clientId) == $c['id']) ? 'selected' : '' ?>>
                                    <?= htmlspecialchars($c['company_name']) ?>
                                </option>
                                <?php endforeach; ?>
                            </select>
                            <?php if ($clientId): ?>
                                <input type="hidden" name="client_id" value="<?= $clientId ?>">
                            <?php endif; ?>
                        </div>
                        
                        <div class="form-group">
                            <label for="name">Nazwa projektu *</label>
                            <input type="text" id="name" name="name" required 
                                value="<?= htmlspecialchars($project['name'] ?? '') ?>">
                        </div>
                        
                        <div class="form-group">
                            <label for="repo_url">URL repozytorium *</label>
                            <input type="url" id="repo_url" name="repo_url" required 
                                value="<?= htmlspecialchars($project['repo_url'] ?? '') ?>">
                            <span class="hint">np. https://github.com/user/repo</span>
                        </div>
                        
                        <div class="form-group">
                            <label for="repo_provider">Provider</label>
                            <select id="repo_provider" name="repo_provider">
                                <?php foreach ($providers as $val => $label): ?>
                                <option value="<?= $val ?>" <?= ($project['repo_provider'] ?? 'github') === $val ? 'selected' : '' ?>><?= $label ?></option>
                                <?php endforeach; ?>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="default_branch">Domyślny branch</label>
                            <input type="text" id="default_branch" name="default_branch" 
                                value="<?= htmlspecialchars($project['default_branch'] ?? 'main') ?>">
                        </div>
                        
                        <div class="form-group">
                            <label for="language_primary">Język programowania</label>
                            <input type="text" id="language_primary" name="language_primary" 
                                value="<?= htmlspecialchars($project['language_primary'] ?? '') ?>">
                            <span class="hint">np. python, javascript, php</span>
                        </div>
                        
                        <div class="form-group">
                            <label for="scan_schedule">Harmonogram skanów</label>
                            <select id="scan_schedule" name="scan_schedule">
                                <?php foreach ($schedules as $val => $label): ?>
                                <option value="<?= $val ?>" <?= ($project['scan_schedule'] ?? 'weekly') === $val ? 'selected' : '' ?>><?= $label ?></option>
                                <?php endforeach; ?>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="status">Status</label>
                            <select id="status" name="status">
                                <?php foreach ($statuses as $val => $label): ?>
                                <option value="<?= $val ?>" <?= ($project['status'] ?? 'active') === $val ? 'selected' : '' ?>><?= $label ?></option>
                                <?php endforeach; ?>
                            </select>
                        </div>
                        
                        <div class="form-group" style="grid-column: 1 / -1;">
                            <label for="auth_token">Token dostępu (opcjonalnie)</label>
                            <input type="password" id="auth_token" name="auth_token" 
                                value="" placeholder="<?= $project ? 'Pozostaw puste aby nie zmieniać' : 'ghp_xxxxxxxxxxxx' ?>">
                            <span class="hint">Token GitHub/GitLab z dostępem do repo. Będzie zaszyfrowany w bazie.</span>
                        </div>
                    </div>
                    
                    <div style="margin-top: 20px;">
                        <button type="submit" class="btn">Zapisz</button>
                        <a href="projects.php<?= $clientId ? '?client_id=' . $clientId : '' ?>" class="btn secondary">Anuluj</a>
                    </div>
                </form>
            </div>
            
        <?php elseif ($action === 'view' && $project): ?>
            <!-- View detail -->
            <?php 
            $projectClient = $clientRepo->find($project['client_id']);
            ?>
            <div class="card project-detail">
                <h2><?= htmlspecialchars($project['name']) ?></h2>
                <span class="badge <?= $project['status'] ?>"><?= $statuses[$project['status']] ?></span>
                
                <div class="detail-grid">
                    <div class="detail-item">
                        <dt>Klient</dt>
                        <dd><a href="clients.php?action=view&id=<?= $projectClient['id'] ?>"><?= htmlspecialchars($projectClient['company_name']) ?></a></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Repozytorium</dt>
                        <dd><a href="<?= htmlspecialchars($project['repo_url']) ?>" target="_blank"><?= htmlspecialchars($project['repo_url']) ?></a></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Provider</dt>
                        <dd><?= $providers[$project['repo_provider']] ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Branch</dt>
                        <dd><code><?= htmlspecialchars($project['default_branch']) ?></code></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Język</dt>
                        <dd><?= htmlspecialchars($project['language_primary'] ?: '-') ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Harmonogram</dt>
                        <dd><?= $schedules[$project['scan_schedule']] ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Lokalna ścieżka</dt>
                        <dd><code><?= htmlspecialchars($project['clone_path']) ?></code></dd>
                    </div>
                    <?php if ($project['last_commit_sha']): ?>
                    <div class="detail-item">
                        <dt>Ostatni commit</dt>
                        <dd><code><?= substr(htmlspecialchars($project['last_commit_sha']), 0, 8) ?></code></dd>
                    </div>
                    <?php endif; ?>
                </div>
                
                <?php if ($project['last_scan_at'] || $project['next_scan_at']): ?>
                <div class="scan-info">
                    <?php if ($project['last_scan_at']): ?>
                        <div style="margin-bottom: 8px;">
                            <span class="label">Ostatni skan:</span>
                            <span class="value"><?= htmlspecialchars($project['last_scan_at']) ?></span>
                        </div>
                    <?php endif; ?>
                    <?php if ($project['next_scan_at']): ?>
                        <div>
                            <span class="label">Następny skan:</span>
                            <span class="value"><?= htmlspecialchars($project['next_scan_at']) ?></span>
                        </div>
                    <?php endif; ?>
                </div>
                <?php endif; ?>
                
                <?php if (!empty($project['last_error'])): ?>
                <div class="alert error" style="margin-top: 15px;">
                    <strong>Ostatni błąd:</strong> <?= htmlspecialchars($project['last_error']) ?>
                </div>
                <?php endif; ?>
                
                <div class="actions-bar">
                    <a href="projects.php?action=edit&id=<?= $project['id'] ?>" class="btn">Edytuj</a>
                    <form method="POST" action="projects.php?action=scan_now&id=<?= $project['id'] ?>" style="display: inline;">
                        <input type="hidden" name="csrf_token" value="<?= $_SESSION['csrf_token'] ?>">
                        <button type="submit" class="btn success">Skanuj teraz</button>
                    </form>
                    <a href="scans.php?project_id=<?= $project['id'] ?>" class="btn secondary">Historia skanów</a>
                    <?php if ($project['status'] === 'active'): ?>
                    <form method="POST" action="projects.php?action=delete&id=<?= $project['id'] ?>" style="display: inline;">
                        <input type="hidden" name="csrf_token" value="<?= $_SESSION['csrf_token'] ?>">
                        <button type="submit" class="btn danger" onclick="return confirm('Wstrzymać ten projekt?');">Wstrzymaj</button>
                    </form>
                    <?php endif; ?>
                    <a href="projects.php<?= $clientId ? '?client_id=' . $clientId : '' ?>" class="btn secondary">Powrót</a>
                </div>
            </div>
            
        <?php else: ?>
            <!-- List -->
            <div class="toolbar">
                <div>
                    <a href="projects.php?action=new<?= $clientId ? '&client_id=' . $clientId : '' ?>" class="btn">+ Nowy projekt</a>
                </div>
                <div>
                    <form method="GET" action="projects.php" style="display: inline;">
                        <?php if ($clientId): ?>
                            <input type="hidden" name="client_id" value="<?= $clientId ?>">
                        <?php endif; ?>
                        <select name="status" onchange="this.form.submit()">
                            <option value="">Wszystkie statusy</option>
                            <?php foreach ($statuses as $val => $label): ?>
                            <option value="<?= $val ?>" <?= $statusFilter === $val ? 'selected' : '' ?>><?= $label ?></option>
                            <?php endforeach; ?>
                        </select>
                        <?php if ($statusFilter): ?>
                            <a href="projects.php<?= $clientId ? '?client_id=' . $clientId : '' ?>" class="btn secondary small">Wyczyść</a>
                        <?php endif; ?>
                    </form>
                </div>
            </div>
            
            <div class="card">
                <?php if (empty($projects)): ?>
                    <p style="text-align: center; color: #666; padding: 40px;">
                        Brak projektów. <a href="projects.php?action=new<?= $clientId ? '&client_id=' . $clientId : '' ?>">Dodaj pierwszy</a>
                    </p>
                <?php else: ?>
                    <table>
                        <thead>
                            <tr>
                                <th>Nazwa</th>
                                <th>Klient</th>
                                <th>Provider</th>
                                <th>Status</th>
                                <th>Ostatni skan</th>
                                <th>Akcje</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($projects as $p): 
                                $pClient = $clientRepo->find($p['client_id']);
                            ?>
                            <tr>
                                <td><strong><?= htmlspecialchars($p['name']) ?></strong></td>
                                <td>
                                    <?php if ($pClient): ?>
                                        <a href="clients.php?action=view&id=<?= $pClient['id'] ?>"><?= htmlspecialchars($pClient['company_name']) ?></a>
                                    <?php else: ?>
                                        <em>Klient usunięty</em>
                                    <?php endif; ?>
                                </td>
                                <td><?= $providers[$p['repo_provider']] ?></td>
                                <td><span class="badge <?= $p['status'] ?>"><?= $statuses[$p['status']] ?></span></td>
                                <td><?= $p['last_scan_at'] ? date('Y-m-d', strtotime($p['last_scan_at'])) : '-' ?></td>
                                <td>
                                    <a href="projects.php?action=view&id=<?= $p['id'] ?>" class="btn small">Zobacz</a>
                                    <form method="POST" action="projects.php?action=scan_now&id=<?= $p['id'] ?>" style="display: inline;">
                                        <input type="hidden" name="csrf_token" value="<?= $_SESSION['csrf_token'] ?>">
                                        <button type="submit" class="btn small success">Skanuj</button>
                                    </form>
                                </td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>
        <?php endif; ?>
    </div>
</body>
</html>
