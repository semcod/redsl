<?php
declare(strict_types=1);

// REDSL Panel — Invoice Generator (cron job)
// Usage: php cron/invoice-generator.php
// Cron setup: 0 6 1 * * cd /var/www/redsl && php cron/invoice-generator.php >> var/logs/invoice-generator.log 2>&1
// Generates invoices on 1st day of month for tickets merged in previous month

require __DIR__ . '/../lib/Database.php';
require __DIR__ . '/../lib/Repository/ClientRepository.php';
require __DIR__ . '/../lib/Repository/TicketRepository.php';
require __DIR__ . '/../lib/Repository/InvoiceRepository.php';
require __DIR__ . '/../lib/Service/PdfGenerator.php';

echo "[" . date('Y-m-d H:i:s') . "] Invoice generator started\n";

$db = Database::connection();
$clients = new ClientRepository($db);
$tickets = new TicketRepository($db);
$invoices = new InvoiceRepository($db);
$pdfGen = new PdfGenerator();

// Calculate period (previous month)
$now = new DateTime();
$periodEnd = (clone $now)->modify('last day of previous month');
$periodStart = (clone $periodEnd)->modify('first day of this month');

$periodStartStr = $periodStart->format('Y-m-d');
$periodEndStr = $periodEnd->format('Y-m-d');

echo "[" . date('Y-m-d H:i:s') . "] Generating invoices for period: {$periodStartStr} - {$periodEndStr}\n";

// Get all active clients with uninvoiced tickets in the period
$activeClients = $clients->list('active', limit: 1000);
$invoicesCreated = 0;
$totalValue = 0;

foreach ($activeClients as $client) {
    $clientId = $client['id'];
    
    // Find merged but uninvoiced tickets for this client in the period
    $uninvoiced = $tickets->findUninvoiced($clientId, $periodStartStr, $periodEndStr);
    
    if (empty($uninvoiced)) {
        continue;
    }
    
    echo "[" . date('Y-m-d H:i:s') . "] Client #{$clientId}: " . count($uninvoiced) . " tickets to invoice\n";
    
    try {
        Database::transaction(function($db) use ($client, $uninvoiced, $invoices, $tickets, $pdfGen, $periodStartStr, $periodEndStr, &$invoicesCreated, &$totalValue) {
            $clientId = $client['id'];
            
            // Calculate totals
            $subtotal = 0;
            foreach ($uninvoiced as $ticket) {
                $subtotal += $ticket['price_pln'];
            }
            
            $vatRate = 23.00;
            $vatAmount = round($subtotal * $vatRate / 100, 2);
            $total = $subtotal + $vatAmount;
            
            // Generate invoice number
            $prefix = getenv('INVOICE_PREFIX') ?: 'FV';
            $number = $invoices->generateNumber($prefix, (int)date('Y'));
            
            // Create invoice
            $issueDate = date('Y-m-d');
            $dueDate = date('Y-m-d', strtotime("+14 days"));
            
            $invoiceId = $invoices->create([
                'client_id' => $clientId,
                'number' => $number,
                'issue_date' => $issueDate,
                'due_date' => $dueDate,
                'period_start' => $periodStartStr,
                'period_end' => $periodEndStr,
                'subtotal_pln' => $subtotal,
                'vat_rate' => $vatRate,
                'vat_amount_pln' => $vatAmount,
                'total_pln' => $total,
                'status' => 'draft',
            ]);
            
            // Add items and link tickets
            foreach ($uninvoiced as $ticket) {
                $description = sprintf('[%s] %s',
                    strtoupper($ticket['type']),
                    mb_strimwidth($ticket['title'], 0, 100, '...')
                );
                
                $invoices->addItem($invoiceId, $ticket['id'], $description, $ticket['price_pln']);
            }
            
            // Generate PDF
            $invoice = $invoices->findWithItems($invoiceId);
            $pdfPath = $pdfGen->generateInvoice($invoice);
            
            // Update with PDF path
            $invoices->update($invoiceId, ['pdf_path' => $pdfPath]);
            
            echo "[" . date('Y-m-d H:i:s') . "]   Created invoice #{$invoiceId}: {$number} = {$total} PLN\n";
            
            $invoicesCreated++;
            $totalValue += $total;
        });
        
    } catch (Throwable $e) {
        echo "[" . date('Y-m-d H:i:s') . "]   ERROR for client #{$clientId}: " . $e->getMessage() . "\n";
    }
}

echo "[" . date('Y-m-d H:i:s') . "] Done. Invoices created: {$invoicesCreated}, Total value: {$totalValue} PLN\n";
exit($invoicesCreated > 0 ? 0 : 0);  // Exit 0 even if no invoices - not an error
