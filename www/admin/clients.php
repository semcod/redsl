<?php
declare(strict_types=1);

require __DIR__ . '/auth.php';
require __DIR__ . '/../lib/Database.php';
require __DIR__ . '/../lib/Repository/ClientRepository.php';

$db = Database::connection();
$repo = new ClientRepository($db);

$action = $_GET['action'] ?? 'list';
$error = '';
$success = '';

// Handle POST actions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    validateCsrfToken();
    
    $id = (int)($_POST['id'] ?? 0);
    
    if ($action === 'save') {
        $data = [
            'company_name' => trim($_POST['company_name'] ?? ''),
            'tax_id' => trim($_POST['tax_id'] ?? ''),
            'regon' => trim($_POST['regon'] ?? ''),
            'address_line1' => trim($_POST['address_line1'] ?? ''),
            'address_line2' => trim($_POST['address_line2'] ?? ''),
            'city' => trim($_POST['city'] ?? ''),
            'postal_code' => trim($_POST['postal_code'] ?? ''),
            'country' => trim($_POST['country'] ?? 'PL'),
            'contact_name' => trim($_POST['contact_name'] ?? ''),
            'contact_email' => trim($_POST['contact_email'] ?? ''),
            'contact_phone' => trim($_POST['contact_phone'] ?? ''),
            'github_login' => trim($_POST['github_login'] ?? ''),
            'status' => $_POST['status'] ?? 'lead',
            'notes' => trim($_POST['notes'] ?? ''),
        ];
        
        // Validation
        if (empty($data['company_name'])) {
            $error = 'Nazwa firmy jest wymagana';
        } elseif (empty($data['contact_email']) || !filter_var($data['contact_email'], FILTER_VALIDATE_EMAIL)) {
            $error = 'Podaj prawidłowy email';
        } else {
            try {
                if ($id > 0) {
                    $repo->update($id, $data);
                    $success = 'Klient zaktualizowany';
                } else {
                    $id = $repo->create($data);
                    $success = 'Klient dodany (ID: ' . $id . ')';
                }
                // Redirect to prevent resubmission
                header('Location: clients.php?success=' . urlencode($success));
                exit;
            } catch (Throwable $e) {
                $error = 'Błąd: ' . $e->getMessage();
            }
        }
    } elseif ($action === 'delete' && $id > 0) {
        try {
            // Soft delete - archive instead
            $repo->archive($id);
            $success = 'Klient zarchiwizowany';
            header('Location: clients.php?success=' . urlencode($success));
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

// Get client for edit
$client = null;
if (($action === 'edit' || $action === 'view') && isset($_GET['id'])) {
    $client = $repo->find((int)$_GET['id']);
}

// List clients
$statusFilter = $_GET['status'] ?? null;
$search = trim($_GET['search'] ?? '');
$page = max(1, (int)($_GET['page'] ?? 1));
$perPage = 20;

if (!empty($search)) {
    $clients = $repo->search($search, $perPage);
    $total = count($clients);
} else {
    $clients = $repo->list($statusFilter, $perPage, ($page - 1) * $perPage);
    // Approximate total for pagination (in production, use COUNT query)
    $total = count($clients) + (($page - 1) * $perPage);
}

$statuses = ['lead' => 'Lead', 'active' => 'Aktywny', 'suspended' => 'Zawieszony', 'archived' => 'Zarchiwizowany'];
?>
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Klienci — REDSL Panel</title>
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
        
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        
        .toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
        .btn { display: inline-block; padding: 10px 20px; background: #1a1a2e; color: white; text-decoration: none; border-radius: 4px; font-size: 14px; border: none; cursor: pointer; }
        .btn:hover { background: #2a2a4e; }
        .btn.secondary { background: #666; }
        .btn.danger { background: #c62828; }
        .btn.small { padding: 5px 10px; font-size: 12px; }
        
        input, select, textarea { padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
        input:focus, select:focus, textarea:focus { outline: none; border-color: #1a1a2e; }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase; background: #fafafa; }
        tr:hover { background: #f9f9f9; }
        .badge { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
        .badge.active { background: #e8f5e9; color: #2e7d32; }
        .badge.lead { background: #e3f2fd; color: #1565c0; }
        .badge.suspended { background: #ffebee; color: #c62828; }
        .badge.archived { background: #f5f5f5; color: #666; }
        
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .form-group { display: flex; flex-direction: column; }
        .form-group label { font-weight: 500; margin-bottom: 5px; font-size: 14px; color: #333; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; }
        .form-group textarea { min-height: 80px; resize: vertical; }
        .form-group .hint { font-size: 12px; color: #666; margin-top: 4px; }
        
        .pagination { display: flex; gap: 10px; margin-top: 20px; }
        .pagination a { padding: 8px 12px; background: white; border-radius: 4px; text-decoration: none; color: #333; }
        .pagination a:hover { background: #1a1a2e; color: white; }
        .pagination .current { padding: 8px 12px; background: #1a1a2e; color: white; border-radius: 4px; }
        
        .client-detail h2 { margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        .detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
        .detail-item dt { font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase; }
        .detail-item dd { margin: 5px 0 0 0; font-size: 16px; }
        .actions-bar { display: flex; gap: 10px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>REDSL Panel — Klienci</h1>
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
        
        <?php if ($action === 'new' || $action === 'edit'): ?>
            <!-- Form -->
            <div class="card">
                <h2><?= $action === 'edit' ? 'Edytuj klienta' : 'Nowy klient' ?></h2>
                <form method="POST" action="clients.php?action=save">
                    <input type="hidden" name="csrf_token" value="<?= $_SESSION['csrf_token'] ?>">
                    <?php if ($client): ?>
                        <input type="hidden" name="id" value="<?= $client['id'] ?>">
                    <?php endif; ?>
                    
                    <div class="form-grid">
                        <div class="form-group">
                            <label for="company_name">Nazwa firmy *</label>
                            <input type="text" id="company_name" name="company_name" required 
                                value="<?= htmlspecialchars($client['company_name'] ?? '') ?>">
                        </div>
                        <div class="form-group">
                            <label for="status">Status</label>
                            <select id="status" name="status">
                                <?php foreach ($statuses as $val => $label): ?>
                                <option value="<?= $val ?>" <?= ($client['status'] ?? 'lead') === $val ? 'selected' : '' ?>><?= $label ?></option>
                                <?php endforeach; ?>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="tax_id">NIP</label>
                            <input type="text" id="tax_id" name="tax_id" 
                                value="<?= htmlspecialchars($client['tax_id'] ?? '') ?>">
                        </div>
                        <div class="form-group">
                            <label for="regon">REGON</label>
                            <input type="text" id="regon" name="regon" 
                                value="<?= htmlspecialchars($client['regon'] ?? '') ?>">
                        </div>
                        <div class="form-group">
                            <label for="contact_name">Osoba kontaktowa</label>
                            <input type="text" id="contact_name" name="contact_name" 
                                value="<?= htmlspecialchars($client['contact_name'] ?? '') ?>">
                        </div>
                        <div class="form-group">
                            <label for="contact_email">Email *</label>
                            <input type="email" id="contact_email" name="contact_email" required 
                                value="<?= htmlspecialchars($client['contact_email'] ?? '') ?>">
                        </div>
                        <div class="form-group">
                            <label for="contact_phone">Telefon</label>
                            <input type="tel" id="contact_phone" name="contact_phone" 
                                value="<?= htmlspecialchars($client['contact_phone'] ?? '') ?>">
                        </div>
                        <div class="form-group">
                            <label for="github_login">GitHub login</label>
                            <input type="text" id="github_login" name="github_login" 
                                value="<?= htmlspecialchars($client['github_login'] ?? '') ?>">
                            <span class="hint">Opcjonalnie - dla OAuth integration</span>
                        </div>
                        <div class="form-group">
                            <label for="address_line1">Adres linia 1</label>
                            <input type="text" id="address_line1" name="address_line1" 
                                value="<?= htmlspecialchars($client['address_line1'] ?? '') ?>">
                        </div>
                        <div class="form-group">
                            <label for="address_line2">Adres linia 2</label>
                            <input type="text" id="address_line2" name="address_line2" 
                                value="<?= htmlspecialchars($client['address_line2'] ?? '') ?>">
                        </div>
                        <div class="form-group">
                            <label for="city">Miasto</label>
                            <input type="text" id="city" name="city" 
                                value="<?= htmlspecialchars($client['city'] ?? '') ?>">
                        </div>
                        <div class="form-group">
                            <label for="postal_code">Kod pocztowy</label>
                            <input type="text" id="postal_code" name="postal_code" 
                                value="<?= htmlspecialchars($client['postal_code'] ?? '') ?>">
                        </div>
                        <div class="form-group">
                            <label for="country">Kraj</label>
                            <input type="text" id="country" name="country" maxlength="2" 
                                value="<?= htmlspecialchars($client['country'] ?? 'PL') ?>">
                            <span class="hint">Kod ISO 2-literowy (PL, DE, etc.)</span>
                        </div>
                    </div>
                    
                    <div class="form-group" style="margin-top: 20px;">
                        <label for="notes">Notatki</label>
                        <textarea id="notes" name="notes"><?= htmlspecialchars($client['notes'] ?? '') ?></textarea>
                    </div>
                    
                    <div style="margin-top: 20px;">
                        <button type="submit" class="btn">Zapisz</button>
                        <a href="clients.php" class="btn secondary">Anuluj</a>
                    </div>
                </form>
            </div>
            
        <?php elseif ($action === 'view' && $client): ?>
            <!-- View detail -->
            <div class="card client-detail">
                <h2><?= htmlspecialchars($client['company_name']) ?></h2>
                <span class="badge <?= $client['status'] ?>"><?= $statuses[$client['status']] ?? $client['status'] ?></span>
                
                <div class="detail-grid" style="margin-top: 20px;">
                    <div class="detail-item">
                        <dt>Email</dt>
                        <dd><?= htmlspecialchars($client['contact_email']) ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Osoba kontaktowa</dt>
                        <dd><?= htmlspecialchars($client['contact_name'] ?: '-') ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Telefon</dt>
                        <dd><?= htmlspecialchars($client['contact_phone'] ?: '-') ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>NIP / REGON</dt>
                        <dd><?= htmlspecialchars($client['tax_id'] ?: '-') ?> / <?= htmlspecialchars($client['regon'] ?: '-') ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Adres</dt>
                        <dd>
                            <?= htmlspecialchars($client['address_line1'] ?: '-') ?><br>
                            <?= $client['address_line2'] ? htmlspecialchars($client['address_line2']) . '<br>' : '' ?>
                            <?= htmlspecialchars($client['postal_code'] ?: '') ?> <?= htmlspecialchars($client['city'] ?: '') ?><br>
                            <?= htmlspecialchars($client['country'] ?: 'PL') ?>
                        </dd>
                    </div>
                    <div class="detail-item">
                        <dt>GitHub</dt>
                        <dd><?= $client['github_login'] ? '<a href="https://github.com/' . htmlspecialchars($client['github_login']) . '" target="_blank">@' . htmlspecialchars($client['github_login']) . '</a>' : '-' ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Dodano</dt>
                        <dd><?= htmlspecialchars($client['created_at']) ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Ostatnia zmiana</dt>
                        <dd><?= htmlspecialchars($client['updated_at']) ?></dd>
                    </div>
                </div>
                
                <?php if (!empty($client['notes'])): ?>
                <div style="margin-top: 20px;">
                    <dt style="font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase;">Notatki</dt>
                    <dd style="margin: 5px 0 0 0; white-space: pre-wrap;"><?= nl2br(htmlspecialchars($client['notes'])) ?></dd>
                </div>
                <?php endif; ?>
                
                <div class="actions-bar">
                    <a href="clients.php?action=edit&id=<?= $client['id'] ?>" class="btn">Edytuj</a>
                    <a href="contracts.php?client_id=<?= $client['id'] ?>" class="btn">Umowy</a>
                    <a href="projects.php?client_id=<?= $client['id'] ?>" class="btn">Projekty</a>
                    <a href="clients.php" class="btn secondary">Powrót</a>
                </div>
            </div>
            
        <?php else: ?>
            <!-- List -->
            <div class="toolbar">
                <div>
                    <a href="clients.php?action=new" class="btn">+ Nowy klient</a>
                </div>
                <div style="display: flex; gap: 10px;">
                    <form method="GET" action="clients.php" style="display: flex; gap: 10px;">
                        <select name="status" onchange="this.form.submit()">
                            <option value="">Wszystkie statusy</option>
                            <?php foreach ($statuses as $val => $label): ?>
                            <option value="<?= $val ?>" <?= $statusFilter === $val ? 'selected' : '' ?>><?= $label ?></option>
                            <?php endforeach; ?>
                        </select>
                        <input type="text" name="search" placeholder="Szukaj..." value="<?= htmlspecialchars($search) ?>">
                        <button type="submit" class="btn">Szukaj</button>
                        <?php if ($statusFilter || $search): ?>
                            <a href="clients.php" class="btn secondary">Wyczyść</a>
                        <?php endif; ?>
                    </form>
                </div>
            </div>
            
            <div class="card">
                <?php if (empty($clients)): ?>
                    <p style="text-align: center; color: #666; padding: 40px;">
                        Brak klientów. <a href="clients.php?action=new">Dodaj pierwszego</a>
                    </p>
                <?php else: ?>
                    <table>
                        <thead>
                            <tr>
                                <th>Firma</th>
                                <th>Email</th>
                                <th>Status</th>
                                <th>Dodano</th>
                                <th>Akcje</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($clients as $c): ?>
                            <tr>
                                <td><strong><?= htmlspecialchars($c['company_name']) ?></strong></td>
                                <td><?= htmlspecialchars($c['contact_email']) ?></td>
                                <td><span class="badge <?= $c['status'] ?>"><?= $statuses[$c['status']] ?></span></td>
                                <td><?= date('Y-m-d', strtotime($c['created_at'])) ?></td>
                                <td>
                                    <a href="clients.php?action=view&id=<?= $c['id'] ?>" class="btn small">Zobacz</a>
                                    <a href="clients.php?action=edit&id=<?= $c['id'] ?>" class="btn small secondary">Edytuj</a>
                                    <?php if ($c['status'] !== 'archived'): ?>
                                    <form method="POST" action="clients.php?action=delete" style="display: inline;" onsubmit="return confirm('Zarchiwizować tego klienta?');">
                                        <input type="hidden" name="csrf_token" value="<?= $_SESSION['csrf_token'] ?>">
                                        <input type="hidden" name="id" value="<?= $c['id'] ?>">
                                        <button type="submit" class="btn small danger">Archiwizuj</button>
                                    </form>
                                    <?php endif; ?>
                                </td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                    
                    <?php if (!$search && $total >= $perPage): ?>
                    <div class="pagination">
                        <?php if ($page > 1): ?>
                            <a href="clients.php?page=<?= $page - 1 ?><?= $statusFilter ? '&status=' . $statusFilter : '' ?>">&larr; Poprzednia</a>
                        <?php endif; ?>
                        <span class="current">Strona <?= $page ?></span>
                        <?php if (count($clients) === $perPage): ?>
                            <a href="clients.php?page=<?= $page + 1 ?><?= $statusFilter ? '&status=' . $statusFilter : '' ?>">Następna &rarr;</a>
                        <?php endif; ?>
                    </div>
                    <?php endif; ?>
                <?php endif; ?>
            </div>
        <?php endif; ?>
    </div>
</body>
</html>
