<?php
declare(strict_types=1);

require __DIR__ . '/auth.php';
require __DIR__ . '/../lib/Database.php';
require __DIR__ . '/../lib/Repository/ClientRepository.php';
require __DIR__ . '/../lib/Repository/InvoiceRepository.php';
require __DIR__ . '/../lib/Service/PdfGenerator.php';

$db = Database::connection();
$clientRepo = new ClientRepository($db);
$invoiceRepo = new InvoiceRepository($db);
$pdfGen = new PdfGenerator();

$action = $_GET['action'] ?? 'list';
$clientId = (int)($_GET['client_id'] ?? 0);
$error = '';
$success = '';

// Handle POST actions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    validateCsrfToken();
    
    $id = (int)($_POST['id'] ?? 0);
    
    if ($action === 'mark_paid' && $id > 0) {
        try {
            $invoiceRepo->markPaid($id, $_POST['payment_method'] ?? 'transfer');
            $success = 'Faktura oznaczona jako opłacona';
            header('Location: invoices.php?success=' . urlencode($success));
            exit;
        } catch (Throwable $e) {
            $error = 'Błąd: ' . $e->getMessage();
        }
    } elseif ($action === 'cancel' && $id > 0) {
        try {
            $invoiceRepo->cancel($id);
            $success = 'Faktura anulowana';
            header('Location: invoices.php?success=' . urlencode($success));
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

// Get invoice for view
$invoice = null;
if ($action === 'view' && isset($_GET['id'])) {
    $invoice = $invoiceRepo->findWithItems((int)$_GET['id']);
}

// Get client if filtering
$client = null;
if ($clientId > 0) {
    $client = $clientRepo->find($clientId);
}

// List invoices
$statusFilter = $_GET['status'] ?? null;
if ($clientId > 0) {
    $invoices = $invoiceRepo->findByClient($clientId, 100);
} else {
    $invoices = $invoiceRepo->list($statusFilter, 100);
}

$statuses = [
    'draft' => 'Szkic',
    'sent' => 'Wysłana',
    'paid' => 'Opłacona',
    'overdue' => 'Przeterminowana',
    'cancelled' => 'Anulowana',
];

// Get summary
$summary = $invoiceRepo->getSummary();
$totalByStatus = [];
foreach ($summary as $s) {
    $totalByStatus[$s['status']] = $s;
}
?>
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Faktury — REDSL Panel</title>
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
        .badge.draft { background: #f5f5f5; color: #666; }
        .badge.sent { background: #fff3e0; color: #e65100; }
        .badge.paid { background: #e8f5e9; color: #2e7d32; }
        .badge.overdue { background: #ffebee; color: #c62828; }
        .badge.cancelled { background: #eeeeee; color: #999; text-decoration: line-through; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-card .number { font-size: 28px; font-weight: bold; color: #1a1a2e; }
        .stat-card .label { color: #666; font-size: 12px; }
        .stat-card .total { font-size: 14px; color: #2e7d32; font-weight: 500; margin-top: 5px; }
        
        .invoice-detail h2 { margin-top: 0; }
        .detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .detail-item dt { font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase; }
        .detail-item dd { margin: 5px 0 0 0; font-size: 16px; }
        
        .items-table { margin: 20px 0; }
        .items-table th { background: #f5f5f5; }
        
        .totals { margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 4px; }
        .totals .row { display: flex; justify-content: space-between; margin: 8px 0; }
        .totals .grand-total { font-size: 18px; font-weight: bold; border-top: 2px solid #333; padding-top: 10px; margin-top: 10px; }
        
        .actions-bar { display: flex; gap: 10px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; flex-wrap: wrap; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>REDSL Panel — Faktury</h1>
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
            </div>
        <?php endif; ?>
        
        <?php if ($action === 'view' && $invoice): ?>
            <!-- View detail -->
            <div class="card invoice-detail">
                <h2>Faktura <?= htmlspecialchars($invoice['number']) ?></h2>
                <span class="badge <?= $invoice['status'] ?>"><?= $statuses[$invoice['status']] ?></span>
                
                <div class="detail-grid">
                    <div class="detail-item">
                        <dt>Klient</dt>
                        <dd><a href="clients.php?action=view&id=<?= $invoice['client_id'] ?>"><?= htmlspecialchars($invoice['company_name']) ?></a></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Data wystawienia</dt>
                        <dd><?= htmlspecialchars($invoice['issue_date']) ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Termin płatności</dt>
                        <dd><?= htmlspecialchars($invoice['due_date']) ?></dd>
                    </div>
                    <div class="detail-item">
                        <dt>Okres</dt>
                        <dd><?= htmlspecialchars($invoice['period_start']) ?> - <?= htmlspecialchars($invoice['period_end']) ?></dd>
                    </div>
                </div>
                
                <h3>Pozycje faktury</h3>
                <table class="items-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Ticket</th>
                            <th>Opis</th>
                            <th style="text-align: right;">Kwota</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($invoice['items'] as $i => $item): ?>
                        <tr>
                            <td><?= $i + 1 ?></td>
                            <td><a href="tickets.php?action=view&id=<?= $item['ticket_id'] ?>">#<?= $item['ticket_id'] ?></a></td>
                            <td><?= htmlspecialchars($item['description']) ?></td>
                            <td style="text-align: right;"><?= number_format($item['amount_pln'], 2) ?> PLN</td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
                
                <div class="totals">
                    <div class="row">
                        <span>Wartość netto:</span>
                        <span><?= number_format($invoice['subtotal_pln'], 2) ?> PLN</span>
                    </div>
                    <div class="row">
                        <span>VAT (<?= $invoice['vat_rate'] ?>%):</span>
                        <span><?= number_format($invoice['vat_amount_pln'], 2) ?> PLN</span>
                    </div>
                    <div class="row grand-total">
                        <span>RAZEM DO ZAPŁATY:</span>
                        <span><?= number_format($invoice['total_pln'], 2) ?> PLN</span>
                    </div>
                </div>
                
                <div class="actions-bar">
                    <?php if ($invoice['status'] === 'draft'): ?>
                        <span class="alert info" style="display: inline-block; margin: 0;">Szkic - zostanie wysłany przez cron</span>
                    <?php elseif ($invoice['status'] === 'sent'): ?>
                        <form method="POST" action="invoices.php?action=mark_paid&id=<?= $invoice['id'] ?>" style="display: inline;">
                            <input type="hidden" name="csrf_token" value="<?= $_SESSION['csrf_token'] ?>">
                            <select name="payment_method" style="width: auto; display: inline-block;">
                                <option value="transfer">Przelew</option>
                                <option value="card">Karta</option>
                                <option value="other">Inne</option>
                            </select>
                            <button type="submit" class="btn success">Oznacz jako opłacona</button>
                        </form>
                    <?php elseif ($invoice['status'] === 'paid'): ?>
                        <span class="alert success" style="display: inline-block; margin: 0;">
                            Opłacona: <?= htmlspecialchars($invoice['paid_at']) ?>
                            (<?= htmlspecialchars($invoice['payment_method']) ?>)
                        </span>
                    <?php endif; ?>
                    
                    <?php if ($invoice['status'] !== 'cancelled' && $invoice['status'] !== 'paid'): ?>
                        <form method="POST" action="invoices.php?action=cancel&id=<?= $invoice['id'] ?>" style="display: inline;">
                            <input type="hidden" name="csrf_token" value="<?= $_SESSION['csrf_token'] ?>">
                            <button type="submit" class="btn danger" onclick="return confirm('Anulować tę fakturę?');">Anuluj</button>
                        </form>
                    <?php endif; ?>
                    
                    <?php if ($invoice['pdf_path']): ?>
                        <a href="<?= htmlspecialchars($invoice['pdf_path']) ?>" target="_blank" class="btn secondary">Pobierz PDF</a>
                    <?php endif; ?>
                    
                    <a href="invoices.php<?= $clientId ? '?client_id=' . $clientId : '' ?>" class="btn secondary">Powrót</a>
                </div>
            </div>
            
        <?php else: ?>
            <!-- Stats -->
            <div class="stats-grid">
                <?php foreach ($statuses as $code => $label): 
                    $stat = $totalByStatus[$code] ?? null;
                ?>
                <div class="stat-card">
                    <div class="number"><?= $stat ? $stat['count'] : 0 ?></div>
                    <div class="label"><?= $label ?></div>
                    <?php if ($stat && $stat['total']): ?>
                    <div class="total"><?= number_format($stat['total'], 0) ?> PLN</div>
                    <?php endif; ?>
                </div>
                <?php endforeach; ?>
            </div>
            
            <!-- List -->
            <div class="toolbar">
                <div>
                    <span style="color: #666;">Faktury generuje automatycznie cron (1. dnia miesiąca)</span>
                </div>
                <div>
                    <form method="GET" action="invoices.php" style="display: inline;">
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
                            <a href="invoices.php<?= $clientId ? '?client_id=' . $clientId : '' ?>" class="btn secondary small">Wyczyść</a>
                        <?php endif; ?>
                    </form>
                </div>
            </div>
            
            <div class="card">
                <?php if (empty($invoices)): ?>
                    <p style="text-align: center; color: #666; padding: 40px;">
                        Brak faktur. Pierwsza zostanie wygenerowana automatycznie po zamknięciu pierwszego ticketu.
                    </p>
                <?php else: ?>
                    <table>
                        <thead>
                            <tr>
                                <th>Numer</th>
                                <th>Klient</th>
                                <th>Data</th>
                                <th>Termin</th>
                                <th>Status</th>
                                <th>Kwota</th>
                                <th>Akcje</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($invoices as $inv): ?>
                            <tr>
                                <td><strong><?= htmlspecialchars($inv['number']) ?></strong></td>
                                <td>
                                    <a href="clients.php?action=view&id=<?= $inv['client_id'] ?>">
                                        <?= htmlspecialchars($inv['client_name']) ?>
                                    </a>
                                </td>
                                <td><?= date('Y-m-d', strtotime($inv['issue_date'])) ?></td>
                                <td><?= date('Y-m-d', strtotime($inv['due_date'])) ?></td>
                                <td><span class="badge <?= $inv['status'] ?>"><?= $statuses[$inv['status']] ?></span></td>
                                <td><?= number_format($inv['total_pln'], 2) ?> PLN</td>
                                <td>
                                    <a href="invoices.php?action=view&id=<?= $inv['id'] ?>" class="btn small">Szczegóły</a>
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
