<?php
declare(strict_types=1);

require __DIR__ . '/auth.php';
require __DIR__ . '/../lib/Database.php';
require __DIR__ . '/../lib/Repository/ClientRepository.php';
require __DIR__ . '/../lib/Repository/ProjectRepository.php';
require __DIR__ . '/../lib/Repository/TicketRepository.php';

$db = Database::connection();
$clientRepo = new ClientRepository($db);
$projectRepo = new ProjectRepository($db);
$ticketRepo = new TicketRepository($db);

$action = $_GET['action'] ?? 'list';
$projectId = (int)($_GET['project_id'] ?? 0);
$clientId = (int)($_GET['client_id'] ?? 0);
$error = '';
$success = '';

// Handle POST actions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    validateCsrfToken();
    
    $id = (int)($_POST['id'] ?? 0);
    
    if ($action === 'approve' && $id > 0) {
        try {
            $ticketRepo->approve($id);
            $success = 'Ticket zaakceptowany - można utworzyć PR';
            header('Location: tickets.php?success=' . urlencode($success));
            exit;
        } catch (Throwable $e) {
            $error = 'Błąd: ' . $e->getMessage();
        }
    } elseif ($action === 'reject' && $id > 0) {
        try {
            $ticketRepo->reject($id);
            $success = 'Ticket odrzucony';
            header('Location: tickets.php?success=' . urlencode($success));
            exit;
        } catch (Throwable $e) {
            $error = 'Błąd: ' . $e->getMessage();
        }
    } elseif ($action === 'mark_merged' && $id > 0) {
        try {
            $ticketRepo->markMerged($id);
            $success = 'Ticket oznaczony jako zmergowany - gotowy do fakturowania';
            header('Location: tickets.php?success=' . urlencode($success));
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

// Get ticket for view
$ticket = null;
if ($action === 'view' && isset($_GET['id'])) {
    $ticket = $ticketRepo->find((int)$_GET['id']);
}

// Get filter context
$project = null;
$client = null;
if ($projectId > 0) {
    $project = $projectRepo->find($projectId);
    $client = $project ? $clientRepo->find($project['client_id']) : null;
} elseif ($clientId > 0) {
    $client = $clientRepo->find($clientId);
}

// List tickets
$statusFilter = $_GET['status'] ?? null;
if ($projectId > 0) {
    $tickets = $ticketRepo->findByProject($projectId, $statusFilter, 100);
} elseif ($clientId > 0) {
    $tickets = $ticketRepo->findByClient($clientId, 100);
} else {
    $tickets = $ticketRepo->list($statusFilter, 100);
}

$statuses = [
    'proposed' => 'Zaproponowany',
    'approved' => 'Zaakceptowany',
    'rejected' => 'Odrzucony',
    'in_progress' => 'W realizacji',
    'pr_open' => 'PR otwarty',
    'merged' => 'Zmergowany',
    'expired' => 'Wygasły',
];

$categories = ['auto' => 'Auto', 'user_defined' => 'Ręczny'];

// Get stats
$stats = $ticketRepo->getStats($projectId > 0 ? $projectId : null);
?>
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tickety — REDSL Panel</title>
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
        .btn.success { background: #2e7d32; }
        .btn.danger { background: #c62828; }
        .btn.small { padding: 5px 10px; font-size: 12px; }
        
        select { padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase; background: #fafafa; }
        tr:hover { background: #f9f9f9; }
        
        .badge { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
        .badge.proposed { background: #e3f2fd; color: #1565c0; }
        .badge.approved { background: #fff3e0; color: #e65100; }
        .badge.rejected { background: #ffebee; color: #c62828; text-decoration: line-through; }
        .badge.pr_open { background: #f3e5f5; color: #7b1fa2; }
        .badge.merged { background: #e8f5e9; color: #2e7d32; }
        .badge.expired { background: #eeeeee; color: #999; }
        
        .badge.category { background: #f5f5f5; color: #666; font-size: 10px; padding: 2px 8px; }
        
        .price { font-weight: 600; color: #2e7d32; }
        .price.high { color: #e65100; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-card .number { font-size: 24px; font-weight: bold; color: #1a1a2e; }
        .stat-card .label { color: #666; font-size: 11px; }
        
        .ticket-detail h2 { margin-top: 0; }
        .detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .detail-item dt { font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase; }
        .detail-item dd { margin: 5px 0 0 0; font-size: 16px; }
        
        .status-flow { display: flex; align-items: center; gap: 8px; margin: 20px 0; flex-wrap: wrap; }
        .status-step { padding: 8px 16px; border-radius: 20px; font-size: 13px; background: #f5f5f5; color: #666; }
        .status-step.active { background: #1a1a2e; color: white; }
        .status-step.completed { background: #e8f5e9; color: #2e7d32; }
        .status-arrow { color: #666; }
        
        .actions-bar { display: flex; gap: 10px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; flex-wrap: wrap; }
        
        .code-block { background: #f5f5f5; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 13px; overflow-x: auto; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>REDSL Panel — Tickety</h1>
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
        
        <?php if ($project): ?>
            <div class="alert info">
                <strong>Projekt:</strong> <?= htmlspecialchars($project['name']) ?> 
                (Klient: <a href="clients.php?action=view&id=<?= $client['id'] ?>"><?= htmlspecialchars($client['company_name']) ?></a>)
            </div>
        <?php elseif ($client): ?>
            <div class="alert info">
                <strong>Klient:</strong> <?= htmlspecialchars($client['company_name']) ?>
            </div>
        <?php endif; ?>
        
        <?php if ($action === 'view' && $ticket): ?>
            <!-- View detail -->
            <?php
            $metricsBefore = json_decode($ticket['metrics_before'] ?? '{}', true);
            $metricsAfter = json_decode($ticket['metrics_after'] ?? '{}', true);
            ?>
            <div class="card ticket-detail">
                <h2>Ticket #<?= $ticket['id'] ?>: <?= htmlspecialchars($ticket['title']) ?></h2>
                <span class="badge <?= $ticket['status'] ?>"><?= $statuses[$ticket['status']] ?></span>
                <span class="badge category"><?= $categories[$ticket['category']] ?></span>
                
                <div class="status-flow">
                    <span class="status-step <?= $ticket['status'] === 'proposed' ? 'active' : 'completed' ?>">Zaproponowany</span>
                    <span class="status-arrow">→</span>
                    <span class="status-step <?= $ticket['status'] === 'approved' ? 'active' : (in_array($ticket['status'], ['pr_open', 'merged', 'in_progress']) ? 'completed' : '') ?>">Zaakceptowany</span>
                    <span class="status-arrow">→</span>
                    <span class="status-step <?= $ticket['status'] === 'pr_open' ? 'active' : ($ticket['status'] === 'merged' ? 'completed' : '') ?>">PR otwarty</span>
                    <span class="status-arrow">→</span>
                    <span class="status-step <?= $ticket['status'] === 'merged' ? 'active' : '' ?>">Zmergowany</span>
                </div>
                
                <div class="detail-grid">
                    <div class="detail-item">
                        <dt>Projekt</dt>
                        <dd><a href="projects.php?action=view&id=<?= $ticket['project_id'] ?>"><?= htmlspecialchars($ticket['project_name']) ?></a></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Klient</dt>
                        <dd><?= htmlspecialchars($ticket['client_name']) ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Typ</dt>
                        <dd><?= htmlspecialchars($ticket['type']) ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Cena</dt>
                        <dd class="price <?= $ticket['price_pln'] >= 100 ? 'high' : '' ?>"><?= number_format($ticket['price_pln'], 2) ?> PLN</dd>
                    </div>
                    <div class="detail-item">
                        <dt>Plik</dt>
                        <dd><code><?= htmlspecialchars($ticket['file_path'] ?: '-') ?></code></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Funkcja</dt>
                        <dd><code><?= htmlspecialchars($ticket['function_name'] ?: '-') ?></code></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Linie</dt>
                        <dd><?= $ticket['line_start'] ? ($ticket['line_start'] . '-' . $ticket['line_end']) : '-' ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Utworzony</dt>
                        <dd><?= htmlspecialchars($ticket['created_at']) ?></dd>
                    </div>
                </div>
                
                <?php if (!empty($metricsBefore)): ?>
                <div class="card" style="margin: 20px 0;">
                    <strong>Metryki (przed/po):</strong>
                    <div class="code-block">
                        Przed: <?= htmlspecialchars(json_encode($metricsBefore, JSON_PRETTY_PRINT)) ?>
                        <?php if (!empty($metricsAfter)): ?>
                        <br><br>Po: <?= htmlspecialchars(json_encode($metricsAfter, JSON_PRETTY_PRINT)) ?>
                        <?php endif; ?>
                    </div>
                </div>
                <?php endif; ?>
                
                <?php if ($ticket['description']): ?>
                <div style="margin-top: 20px;">
                    <strong>Opis:</strong>
                    <p style="white-space: pre-wrap; background: #f9f9f9; padding: 15px; border-radius: 4px;"><?= nl2br(htmlspecialchars($ticket['description'])) ?></p>
                </div>
                <?php endif; ?>
                
                <?php if ($ticket['pr_url']): ?>
                <div class="alert info" style="margin-top: 20px;">
                    <strong>Pull Request:</strong> <a href="<?= htmlspecialchars($ticket['pr_url']) ?>" target="_blank"><?= htmlspecialchars($ticket['pr_url']) ?></a>
                </div>
                <?php endif; ?>
                
                <div class="actions-bar">
                    <?php if ($ticket['status'] === 'proposed'): ?>
                        <form method="POST" action="tickets.php?action=approve&id=<?= $ticket['id'] ?>" style="display: inline;">
                            <input type="hidden" name="csrf_token" value="<?= $_SESSION['csrf_token'] ?>">
                            <button type="submit" class="btn success">Zaakceptuj</button>
                        </form>
                        <form method="POST" action="tickets.php?action=reject&id=<?= $ticket['id'] ?>" style="display: inline;">
                            <input type="hidden" name="csrf_token" value="<?= $_SESSION['csrf_token'] ?>">
                            <button type="submit" class="btn danger" onclick="return confirm('Odrzucić ten ticket?');">Odrzuć</button>
                        </form>
                    <?php elseif ($ticket['status'] === 'approved'): ?>
                        <span class="alert info" style="display: inline-block; margin: 0;">Gotowy do utworzenia PR (wkrótce: integracja z GitHub)</span>
                    <?php elseif ($ticket['status'] === 'pr_open'): ?>
                        <form method="POST" action="tickets.php?action=mark_merged&id=<?= $ticket['id'] ?>" style="display: inline;">
                            <input type="hidden" name="csrf_token" value="<?= $_SESSION['csrf_token'] ?>">
                            <button type="submit" class="btn success">Oznacz jako zmergowany</button>
                        </form>
                    <?php elseif ($ticket['status'] === 'merged' && !$ticket['invoice_item_id']): ?>
                        <span class="alert success" style="display: inline-block; margin: 0;">Gotowy do fakturowania</span>
                    <?php elseif ($ticket['invoice_item_id']): ?>
                        <span class="badge" style="background: #e8f5e9;">Zafakturowany</span>
                    <?php endif; ?>
                    
                    <a href="tickets.php<?= $projectId ? '?project_id=' . $projectId : ($clientId ? '?client_id=' . $clientId : '') ?>" class="btn secondary">Powrót</a>
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
                    <?php if ($stat['total_value']): ?>
                    <div style="font-size: 12px; color: #666; margin-top: 5px;"><?= number_format($stat['total_value'], 0) ?> PLN</div>
                    <?php endif; ?>
                </div>
                <?php endforeach; ?>
            </div>
            <?php endif; ?>
            
            <!-- List -->
            <div class="toolbar">
                <div>
                    <a href="projects.php" class="btn">Nowy ticket (wybierz projekt)</a>
                </div>
                <div>
                    <form method="GET" action="tickets.php" style="display: inline;">
                        <?php if ($projectId): ?>
                            <input type="hidden" name="project_id" value="<?= $projectId ?>">
                        <?php endif; ?>
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
                            <a href="tickets.php<?= $projectId ? '?project_id=' . $projectId : ($clientId ? '?client_id=' . $clientId : '') ?>" class="btn secondary small">Wyczyść</a>
                        <?php endif; ?>
                    </form>
                </div>
            </div>
            
            <div class="card">
                <?php if (empty($tickets)): ?>
                    <p style="text-align: center; color: #666; padding: 40px;">
                        Brak ticketów. <a href="projects.php">Wybierz projekt aby wygenerować</a>
                    </p>
                <?php else: ?>
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Tytuł</th>
                                <th>Projekt</th>
                                <th>Status</th>
                                <th>Cena</th>
                                <th>Akcje</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($tickets as $t): ?>
                            <tr>
                                <td>#<?= $t['id'] ?></td>
                                <td>
                                    <?= htmlspecialchars(mb_strimwidth($t['title'], 0, 60, '...')) ?>
                                    <span class="badge category" style="margin-left: 8px;"><?= $categories[$t['category']] ?></span>
                                </td>
                                <td><a href="projects.php?action=view&id=<?= $t['project_id'] ?>"><?= htmlspecialchars($t['project_name']) ?></a></td>
                                <td><span class="badge <?= $t['status'] ?>"><?= $statuses[$t['status']] ?></span></td>
                                <td class="price <?= $t['price_pln'] >= 100 ? 'high' : '' ?>"><?= number_format($t['price_pln'], 2) ?> PLN</td>
                                <td>
                                    <a href="tickets.php?action=view&id=<?= $t['id'] ?>" class="btn small">Szczegóły</a>
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
