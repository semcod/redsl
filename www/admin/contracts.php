<?php
declare(strict_types=1);

require __DIR__ . '/auth.php';
require __DIR__ . '/../lib/Database.php';
require __DIR__ . '/../lib/Repository/ClientRepository.php';
require __DIR__ . '/../lib/Repository/ContractRepository.php';

$db = Database::connection();
$clientRepo = new ClientRepository($db);
$contractRepo = new ContractRepository($db);

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
            'type' => $_POST['type'] ?? 'nda',
            'status' => $_POST['status'] ?? 'draft',
            'valid_until' => !empty($_POST['valid_until']) ? $_POST['valid_until'] : null,
            'metadata' => json_encode([
                'template' => $_POST['template'] ?? 'standard',
                'notes' => trim($_POST['notes'] ?? ''),
            ]),
        ];
        
        if ($data['client_id'] <= 0) {
            $error = 'Wybierz klienta';
        } else {
            try {
                if ($id > 0) {
                    $contractRepo->update($id, $data);
                    $success = 'Umowa zaktualizowana';
                } else {
                    // Generate contract number
                    $data['number'] = $contractRepo->generateNumber($data['type'], (int)date('Y'));
                    $id = $contractRepo->create($data);
                    $success = 'Umowa utworzona: ' . $data['number'];
                }
                header('Location: contracts.php?success=' . urlencode($success));
                exit;
            } catch (Throwable $e) {
                $error = 'Błąd: ' . $e->getMessage();
            }
        }
    } elseif ($action === 'send' && $id > 0) {
        // Mark as sent - in production, this would generate PDF and send email
        try {
            $pdfPath = sprintf('var/contracts/%s.pdf', date('Y/m'));
            if (!is_dir($pdfPath)) mkdir($pdfPath, 0750, true);
            $pdfFile = $pdfPath . '/contract-' . $id . '.pdf';
            
            // TODO: Generate actual PDF here
            file_put_contents($pdfFile, 'PDF placeholder - ' . date('Y-m-d H:i:s'));
            
            $contractRepo->markSent($id, $pdfFile);
            $success = 'Umowa oznaczona jako wysłana';
            header('Location: contracts.php?success=' . urlencode($success));
            exit;
        } catch (Throwable $e) {
            $error = 'Błąd: ' . $e->getMessage();
        }
    } elseif ($action === 'sign' && $id > 0) {
        try {
            $contractRepo->markSigned($id);
            $success = 'Umowa oznaczona jako podpisana';
            header('Location: contracts.php?success=' . urlencode($success));
            exit;
        } catch (Throwable $e) {
            $error = 'Błąd: ' . $e->getMessage();
        }
    } elseif ($action === 'cancel' && $id > 0) {
        try {
            $contractRepo->cancel($id);
            $success = 'Umowa anulowana';
            header('Location: contracts.php?success=' . urlencode($success));
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

// Get contract for edit/view
$contract = null;
if (($action === 'edit' || $action === 'view') && isset($_GET['id'])) {
    $contract = $contractRepo->find((int)$_GET['id']);
}

// Get client if filtering by client
$client = null;
if ($clientId > 0) {
    $client = $clientRepo->find($clientId);
}

// List contracts
$statusFilter = $_GET['status'] ?? null;
if ($clientId > 0) {
    $contracts = $contractRepo->findByClient($clientId);
} else {
    $contracts = $contractRepo->list($statusFilter, 100);
}

$types = ['nda' => 'NDA', 'service' => 'Umowa o pracę/usługi', 'addendum' => 'Aneks'];
$statuses = [
    'draft' => 'Szkic', 
    'sent' => 'Wysłana', 
    'signed' => 'Podpisana', 
    'expired' => 'Wygasła',
    'cancelled' => 'Anulowana'
];

// Get all clients for dropdown
$allClients = $clientRepo->list(limit: 1000);
?>
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Umowy — REDSL Panel</title>
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
        .badge.draft { background: #f5f5f5; color: #666; }
        .badge.sent { background: #fff3e0; color: #e65100; }
        .badge.signed { background: #e8f5e9; color: #2e7d32; }
        .badge.expired { background: #ffebee; color: #c62828; }
        .badge.cancelled { background: #eeeeee; color: #666; text-decoration: line-through; }
        
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; font-weight: 500; margin-bottom: 5px; font-size: 14px; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; max-width: 400px; }
        .form-group textarea { min-height: 80px; resize: vertical; }
        .form-group .hint { font-size: 12px; color: #666; margin-top: 4px; }
        
        .contract-detail h2 { margin-top: 0; }
        .detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .detail-item dt { font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase; }
        .detail-item dd { margin: 5px 0 0 0; font-size: 16px; }
        .actions-bar { display: flex; gap: 10px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; flex-wrap: wrap; }
        
        .status-flow { display: flex; align-items: center; gap: 10px; margin: 20px 0; }
        .status-step { padding: 8px 16px; border-radius: 20px; font-size: 14px; background: #f5f5f5; color: #666; }
        .status-step.active { background: #1a1a2e; color: white; }
        .status-step.completed { background: #e8f5e9; color: #2e7d32; }
        .status-arrow { color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>REDSL Panel — Umowy</h1>
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
                <h2><?= $action === 'edit' ? 'Edytuj umowę' : 'Nowa umowa' ?></h2>
                <form method="POST" action="contracts.php?action=save<?= $clientId ? '&client_id=' . $clientId : '' ?>">
                    <input type="hidden" name="csrf_token" value="<?= $_SESSION['csrf_token'] ?>">
                    <?php if ($contract): ?>
                        <input type="hidden" name="id" value="<?= $contract['id'] ?>">
                    <?php endif; ?>
                    
                    <div class="form-group">
                        <label for="client_id">Klient *</label>
                        <select id="client_id" name="client_id" required <?= $clientId ? 'disabled' : '' ?>>
                            <option value="">-- Wybierz klienta --</option>
                            <?php foreach ($allClients as $c): ?>
                            <option value="<?= $c['id'] ?>" <?= (($contract['client_id'] ?? $clientId) == $c['id']) ? 'selected' : '' ?>>
                                <?= htmlspecialchars($c['company_name']) ?> (<?= htmlspecialchars($c['contact_email']) ?>)
                            </option>
                            <?php endforeach; ?>
                        </select>
                        <?php if ($clientId): ?>
                            <input type="hidden" name="client_id" value="<?= $clientId ?>">
                        <?php endif; ?>
                    </div>
                    
                    <div class="form-group">
                        <label for="type">Typ umowy *</label>
                        <select id="type" name="type" required>
                            <?php foreach ($types as $val => $label): ?>
                            <option value="<?= $val ?>" <?= ($contract['type'] ?? 'nda') === $val ? 'selected' : '' ?>><?= $label ?></option>
                            <?php endforeach; ?>
                        </select>
                    </div>
                    
                    <?php if ($action === 'edit'): ?>
                    <div class="form-group">
                        <label for="status">Status</label>
                        <select id="status" name="status">
                            <?php foreach ($statuses as $val => $label): ?>
                            <option value="<?= $val ?>" <?= ($contract['status'] ?? 'draft') === $val ? 'selected' : '' ?>><?= $label ?></option>
                            <?php endforeach; ?>
                        </select>
                    </div>
                    <?php endif; ?>
                    
                    <div class="form-group">
                        <label for="valid_until">Ważna do</label>
                        <input type="date" id="valid_until" name="valid_until" 
                            value="<?= htmlspecialchars($contract['valid_until'] ?? '') ?>">
                        <span class="hint">Data wygaśnięcia umowy (opcjonalnie)</span>
                    </div>
                    
                    <div class="form-group">
                        <label for="template">Szablon</label>
                        <select id="template" name="template">
                            <option value="standard">Standardowy NDA</option>
                            <option value="custom">Niestandardowy</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="notes">Notatki wewnętrzne</label>
                        <textarea id="notes" name="notes"><?= htmlspecialchars(json_decode($contract['metadata'] ?? '{}', true)['notes'] ?? '') ?></textarea>
                    </div>
                    
                    <div style="margin-top: 20px;">
                        <button type="submit" class="btn">Zapisz</button>
                        <a href="contracts.php<?= $clientId ? '?client_id=' . $clientId : '' ?>" class="btn secondary">Anuluj</a>
                    </div>
                </form>
            </div>
            
        <?php elseif ($action === 'view' && $contract): ?>
            <!-- View detail -->
            <?php 
            $contractClient = $clientRepo->find($contract['client_id']);
            $metadata = json_decode($contract['metadata'] ?? '{}', true);
            ?>
            <div class="card contract-detail">
                <h2>Umowa <?= htmlspecialchars($contract['number']) ?></h2>
                <span class="badge <?= $contract['status'] ?>"><?= $statuses[$contract['status']] ?></span>
                
                <div class="status-flow">
                    <span class="status-step <?= $contract['status'] === 'draft' ? 'active' : ($contract['status'] !== 'cancelled' ? 'completed' : '') ?>">Szkic</span>
                    <span class="status-arrow">→</span>
                    <span class="status-step <?= $contract['status'] === 'sent' ? 'active' : (in_array($contract['status'], ['signed', 'expired']) ? 'completed' : '') ?>">Wysłana</span>
                    <span class="status-arrow">→</span>
                    <span class="status-step <?= $contract['status'] === 'signed' ? 'active' : '' ?>">Podpisana</span>
                </div>
                
                <div class="detail-grid">
                    <div class="detail-item">
                        <dt>Klient</dt>
                        <dd><a href="clients.php?action=view&id=<?= $contractClient['id'] ?>"><?= htmlspecialchars($contractClient['company_name']) ?></a></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Typ</dt>
                        <dd><?= $types[$contract['type']] ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Numer</dt>
                        <dd><?= htmlspecialchars($contract['number']) ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Utworzona</dt>
                        <dd><?= date('Y-m-d', strtotime($contract['created_at'])) ?></dd>
                    </div>
                    <?php if ($contract['sent_at']): ?>
                    <div class="detail-item">
                        <dt>Wysłana</dt>
                        <dd><?= date('Y-m-d H:i', strtotime($contract['sent_at'])) ?></dd>
                    </div>
                    <?php endif; ?>
                    <?php if ($contract['signed_at']): ?>
                    <div class="detail-item">
                        <dt>Podpisana</dt>
                        <dd><?= date('Y-m-d H:i', strtotime($contract['signed_at'])) ?></dd>
                    </div>
                    <?php endif; ?>
                    <?php if ($contract['valid_until']): ?>
                    <div class="detail-item">
                        <dt>Ważna do</dt>
                        <dd><?= htmlspecialchars($contract['valid_until']) ?></dd>
                    </div>
                    <?php endif; ?>
                    <?php if ($contract['access_token']): ?>
                    <div class="detail-item">
                        <dt>Link publiczny</dt>
                        <dd><code><?= htmlspecialchars($contract['access_token']) ?></code></dd>
                    </div>
                    <?php endif; ?>
                </div>
                
                <?php if (!empty($metadata['notes'])): ?>
                <div style="margin-top: 20px;">
                    <dt style="font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase;">Notatki</dt>
                    <dd style="margin: 5px 0 0 0; white-space: pre-wrap;"><?= nl2br(htmlspecialchars($metadata['notes'])) ?></dd>
                </div>
                <?php endif; ?>
                
                <div class="actions-bar">
                    <a href="contracts.php?action=edit&id=<?= $contract['id'] ?>" class="btn">Edytuj</a>
                    
                    <?php if ($contract['status'] === 'draft'): ?>
                    <form method="POST" action="contracts.php?action=send&id=<?= $contract['id'] ?>" style="display: inline;">
                        <input type="hidden" name="csrf_token" value="<?= $_SESSION['csrf_token'] ?>">
                        <button type="submit" class="btn success" onclick="return confirm('Oznaczyć jako wysłana? (w produkcji: wyśle email)');">Wyślij</button>
                    </form>
                    <?php endif; ?>
                    
                    <?php if ($contract['status'] === 'sent'): ?>
                    <form method="POST" action="contracts.php?action=sign&id=<?= $contract['id'] ?>" style="display: inline;">
                        <input type="hidden" name="csrf_token" value="<?= $_SESSION['csrf_token'] ?>">
                        <button type="submit" class="btn success" onclick="return confirm('Oznaczyć jako podpisana?');">Oznacz podpisaną</button>
                    </form>
                    <?php endif; ?>
                    
                    <?php if (in_array($contract['status'], ['draft', 'sent'])): ?>
                    <form method="POST" action="contracts.php?action=cancel&id=<?= $contract['id'] ?>" style="display: inline;">
                        <input type="hidden" name="csrf_token" value="<?= $_SESSION['csrf_token'] ?>">
                        <button type="submit" class="btn danger" onclick="return confirm('Anulować tę umowę?');">Anuluj</button>
                    </form>
                    <?php endif; ?>
                    
                    <a href="contracts.php<?= $clientId ? '?client_id=' . $clientId : '' ?>" class="btn secondary">Powrót</a>
                </div>
            </div>
            
        <?php else: ?>
            <!-- List -->
            <div class="toolbar">
                <div>
                    <a href="contracts.php?action=new<?= $clientId ? '&client_id=' . $clientId : '' ?>" class="btn">+ Nowa umowa</a>
                </div>
                <div>
                    <form method="GET" action="contracts.php" style="display: inline;">
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
                            <a href="contracts.php<?= $clientId ? '?client_id=' . $clientId : '' ?>" class="btn secondary small">Wyczyść</a>
                        <?php endif; ?>
                    </form>
                </div>
            </div>
            
            <div class="card">
                <?php if (empty($contracts)): ?>
                    <p style="text-align: center; color: #666; padding: 40px;">
                        Brak umów. <a href="contracts.php?action=new<?= $clientId ? '&client_id=' . $clientId : '' ?>">Utwórz pierwszą</a>
                    </p>
                <?php else: ?>
                    <table>
                        <thead>
                            <tr>
                                <th>Numer</th>
                                <th>Klient</th>
                                <th>Typ</th>
                                <th>Status</th>
                                <th>Utworzona</th>
                                <th>Akcje</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($contracts as $c): 
                                $cClient = $clientRepo->find($c['client_id']);
                            ?>
                            <tr>
                                <td><strong><?= htmlspecialchars($c['number']) ?></strong></td>
                                <td>
                                    <?php if ($cClient): ?>
                                        <a href="clients.php?action=view&id=<?= $cClient['id'] ?>"><?= htmlspecialchars($cClient['company_name']) ?></a>
                                    <?php else: ?>
                                        <em>Klient usunięty</em>
                                    <?php endif; ?>
                                </td>
                                <td><?= $types[$c['type']] ?></td>
                                <td><span class="badge <?= $c['status'] ?>"><?= $statuses[$c['status']] ?></span></td>
                                <td><?= date('Y-m-d', strtotime($c['created_at'])) ?></td>
                                <td>
                                    <a href="contracts.php?action=view&id=<?= $c['id'] ?>" class="btn small">Zobacz</a>
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
