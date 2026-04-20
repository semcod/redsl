<?php
declare(strict_types=1);

require __DIR__ . '/auth.php';
require __DIR__ . '/../lib/Database.php';
require __DIR__ . '/../lib/Repository/ClientRepository.php';
require __DIR__ . '/../lib/Repository/ProjectRepository.php';
require __DIR__ . '/../lib/Repository/ScanRunRepository.php';

$db = Database::connection();
$clientRepo = new ClientRepository($db);
$projectRepo = new ProjectRepository($db);
$scanRepo = new ScanRunRepository($db);

$action = $_GET['action'] ?? 'list';
$projectId = (int)($_GET['project_id'] ?? 0);
$scanId = (int)($_GET['id'] ?? 0);

// Get scan for view
$scan = null;
if ($action === 'view' && $scanId > 0) {
    $scan = $scanRepo->find($scanId);
}

// Get project if filtering
$project = null;
if ($projectId > 0) {
    $project = $projectRepo->find($projectId);
}

// List scans
$statusFilter = $_GET['status'] ?? null;
if ($projectId > 0) {
    $scans = $scanRepo->findByProject($projectId, 50);
} else {
    $scans = $scanRepo->list($statusFilter, 100);
}

$statuses = [
    'queued' => 'W kolejce',
    'cloning' => 'Klonowanie',
    'running' => 'Skanowanie',
    'parsing' => 'Analiza',
    'completed' => 'Zakończony',
    'failed' => 'Błąd',
];

// Get stats
$stats = $scanRepo->getStats();
?>
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Skany — REDSL Panel</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #1a1a2e; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .header h1 { margin: 0; font-size: 24px; }
        .header .nav { margin-top: 10px; }
        .header .nav a { color: #64b5f6; text-decoration: none; margin-right: 20px; }
        .header .nav a:hover { text-decoration: underline; }
        
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        
        .toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
        .btn { display: inline-block; padding: 10px 20px; background: #1a1a2e; color: white; text-decoration: none; border-radius: 4px; font-size: 14px; border: none; cursor: pointer; }
        .btn:hover { background: #2a2a4e; }
        .btn.secondary { background: #666; }
        .btn.small { padding: 5px 10px; font-size: 12px; }
        
        input, select { padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase; background: #fafafa; }
        tr:hover { background: #f9f9f9; }
        
        .badge { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
        .badge.queued { background: #f5f5f5; color: #666; }
        .badge.cloning { background: #e3f2fd; color: #1565c0; }
        .badge.running { background: #fff3e0; color: #e65100; }
        .badge.parsing { background: #f3e5f5; color: #7b1fa2; }
        .badge.completed { background: #e8f5e9; color: #2e7d32; }
        .badge.failed { background: #ffebee; color: #c62828; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-card .number { font-size: 28px; font-weight: bold; color: #1a1a2e; }
        .stat-card .label { color: #666; font-size: 12px; }
        
        .scan-detail h2 { margin-top: 0; }
        .detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 20px 0; }
        .detail-item dt { font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase; }
        .detail-item dd { margin: 5px 0 0 0; font-size: 16px; }
        
        .metrics-box { background: #f5f5f5; padding: 15px; border-radius: 4px; margin-top: 15px; }
        .metrics-box pre { margin: 0; font-size: 13px; overflow-x: auto; }
        
        .log-box { background: #1a1a2e; color: #00ff00; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 13px; max-height: 400px; overflow-y: auto; margin-top: 15px; }
        .log-box .error { color: #ff6666; }
        
        .progress-bar { height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; margin-top: 10px; }
        .progress-bar .fill { height: 100%; background: #3b82f6; transition: width 0.3s; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>REDSL Panel — Skany</h1>
            <div class="nav">
                <a href="index.php">Dashboard</a>
                <a href="clients.php">Klienci</a>
                <a href="contracts.php">Umowy</a>
                <a href="projects.php">Projekty</a>
                <a href="scans.php">Skany</a>
                <a href="invoices.php">Faktury</a>
            </div>
        </div>
        
        <?php if ($project): ?>
            <div class="card" style="background: #e3f2fd;">
                <strong>Projekt:</strong> <?= htmlspecialchars($project['name']) ?> 
                (<a href="projects.php?action=view&id=<?= $project['id'] ?>">zobacz projekt</a>)
            </div>
        <?php endif; ?>
        
        <?php if ($action === 'view' && $scan): ?>
            <!-- View detail -->
            <div class="card scan-detail">
                <h2>Skan #<?= $scan['id'] ?></h2>
                <span class="badge <?= $scan['status'] ?>"><?= $statuses[$scan['status']] ?></span>
                
                <div class="detail-grid">
                    <div class="detail-item">
                        <dt>Projekt</dt>
                        <dd><a href="projects.php?action=view&id=<?= $scan['project_id'] ?>"><?= htmlspecialchars($scan['project_name']) ?></a></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Klient</dt>
                        <dd><?= htmlspecialchars($scan['client_name']) ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Rozpoczęto</dt>
                        <dd><?= htmlspecialchars($scan['started_at']) ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Zakończono</dt>
                        <dd><?= $scan['finished_at'] ? htmlspecialchars($scan['finished_at']) : '-' ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Czas trwania</dt>
                        <dd><?= $scan['duration_sec'] ? sprintf('%d min %d sek', floor($scan['duration_sec']/60), $scan['duration_sec']%60) : '-' ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Commit SHA</dt>
                        <dd><code><?= $scan['commit_sha'] ? substr(htmlspecialchars($scan['commit_sha']), 0, 8) : '-' ?></code></dd>
                    </div>
                </div>
                
                <?php if ($scan['metrics_summary']): 
                    $metrics = json_decode($scan['metrics_summary'], true);
                ?>
                <div class="metrics-box">
                    <strong>Metryki:</strong>
                    <pre><?= htmlspecialchars(json_encode($metrics, JSON_PRETTY_PRINT)) ?></pre>
                </div>
                <?php endif; ?>
                
                <?php if ($scan['error_message']): ?>
                <div class="metrics-box" style="background: #ffebee;">
                    <strong style="color: #c62828;">Błąd:</strong>
                    <pre style="color: #c62828;"><?= htmlspecialchars($scan['error_message']) ?></pre>
                </div>
                <?php endif; ?>
                
                <div style="margin-top: 20px;">
                    <a href="scans.php<?= $projectId ? '?project_id=' . $projectId : '' ?>" class="btn secondary">Powrót</a>
                    <?php if ($scan['artifacts_path'] && is_dir($scan['artifacts_path'])): ?>
                        <a href="api/download-artifacts.php?scan_id=<?= $scan['id'] ?>" class="btn">Pobierz artefakty</a>
                    <?php endif; ?>
                </div>
            </div>
            
        <?php else: ?>
            <!-- Stats -->
            <?php if (!empty($stats)): ?>
            <div class="stats-grid">
                <?php foreach ($stats as $stat): ?>
                <div class="stat-card">
                    <div class="number"><?= $stat['count'] ?></div>
                    <div class="label"><?= $statuses[$stat['status']] ?? $stat['status'] ?></div>
                </div>
                <?php endforeach; ?>
            </div>
            <?php endif; ?>
            
            <!-- List -->
            <div class="toolbar">
                <div>
                    <a href="projects.php" class="btn">Nowy skan (wybierz projekt)</a>
                </div>
                <div>
                    <form method="GET" action="scans.php" style="display: inline;">
                        <?php if ($projectId): ?>
                            <input type="hidden" name="project_id" value="<?= $projectId ?>">
                        <?php endif; ?>
                        <select name="status" onchange="this.form.submit()">
                            <option value="">Wszystkie statusy</option>
                            <?php foreach ($statuses as $val => $label): ?>
                            <option value="<?= $val ?>" <?= $statusFilter === $val ? 'selected' : '' ?>><?= $label ?></option>
                            <?php endforeach; ?>
                        </select>
                        <?php if ($statusFilter): ?>
                            <a href="scans.php<?= $projectId ? '?project_id=' . $projectId : '' ?>" class="btn secondary small">Wyczyść</a>
                        <?php endif; ?>
                    </form>
                </div>
            </div>
            
            <div class="card">
                <?php if (empty($scans)): ?>
                    <p style="text-align: center; color: #666; padding: 40px;">
                        Brak skanów. <a href="projects.php">Wybierz projekt aby zeskanować</a>
                    </p>
                <?php else: ?>
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Projekt</th>
                                <th>Klient</th>
                                <th>Status</th>
                                <th>Rozpoczęto</th>
                                <th>Czas</th>
                                <th>Akcje</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($scans as $s): ?>
                            <tr>
                                <td>#<?= $s['id'] ?></td>
                                <td><a href="projects.php?action=view&id=<?= $s['project_id'] ?>"><?= htmlspecialchars($s['project_name']) ?></a></td>
                                <td><?= htmlspecialchars($s['client_name']) ?></td>
                                <td><span class="badge <?= $s['status'] ?>"><?= $statuses[$s['status']] ?></span></td>
                                <td><?= date('Y-m-d H:i', strtotime($s['started_at'])) ?></td>
                                <td><?= $s['duration_sec'] ? sprintf('%d:%02d', floor($s['duration_sec']/60), $s['duration_sec']%60) : '-' ?></td>
                                <td>
                                    <a href="scans.php?action=view&id=<?= $s['id'] ?>" class="btn small">Szczegóły</a>
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
