<?php
declare(strict_types=1);

// REDSL Panel — Scan Worker (cron job)
// Usage: php cron/scan-worker.php
// Cron setup: */10 * * * * cd /var/www/redsl && php cron/scan-worker.php >> var/logs/scan-worker.log 2>&1
// Finds projects due for scanning and processes them sequentially.
// Uses flock to prevent concurrent runs.

// Prevent concurrent runs
$lockFile = __DIR__ . '/../var/scan-worker.lock';
$lock = fopen($lockFile, 'c');
if (!$lock || !flock($lock, LOCK_EX | LOCK_NB)) {
    echo "[" . date('Y-m-d H:i:s') . "] Another worker is running, exiting.\n";
    exit(0);
}

echo "[" . date('Y-m-d H:i:s') . "] Scan worker started\n";

// Load dependencies
require __DIR__ . '/../lib/Database.php';
require __DIR__ . '/../lib/Encryption.php';
require __DIR__ . '/../lib/Repository/ClientRepository.php';
require __DIR__ . '/../lib/Repository/ProjectRepository.php';
require __DIR__ . '/../lib/Repository/ScanRunRepository.php';
require __DIR__ . '/../lib/Service/GithubClient.php';
require __DIR__ . '/../lib/Service/RedslRunner.php';

// Initialize
$db = Database::connection();
$projects = new ProjectRepository($db);
$scans = new ScanRunRepository($db);
$github = new GithubClient();
$runner = new RedslRunner(timeoutSec: 600);

// Find projects due for scanning
$dueProjects = $projects->findDueForScan(maxN: 5);
echo "[" . date('Y-m-d H:i:s') . "] Found " . count($dueProjects) . " projects due for scan\n";

$successCount = 0;
$failCount = 0;

foreach ($dueProjects as $project) {
    $projectId = $project['id'];
    $projectName = $project['name'];
    
    echo "\n[" . date('Y-m-d H:i:s') . "] >>> Project #{$projectId}: {$projectName}\n";
    
    // Create scan run record
    $scanRun = $scans->create($projectId);
    $scanId = $scanRun['id'];
    echo "[" . date('Y-m-d H:i:s') . "] Scan run created: #{$scanId}\n";
    
    $startTime = time();
    
    try {
        // Step 1: Clone/pull repository
        $scans->updateStatus($scanId, 'cloning');
        echo "[" . date('Y-m-d H:i:s') . "] Cloning repository...\n";
        
        $token = '';
        if (!empty($project['auth_token_encrypted']) && !empty($project['auth_token_nonce'])) {
            $token = Encryption::decrypt($project['auth_token_encrypted'], $project['auth_token_nonce']);
        }
        
        $clonePath = $github->cloneOrPull($project['repo_url'], $token, $project['clone_path']);
        $commitSha = $github->currentCommitSha($clonePath);
        
        echo "[" . date('Y-m-d H:i:s') . "] Cloned to: {$clonePath}\n";
        echo "[" . date('Y-m-d H:i:s') . "] Current commit: " . substr($commitSha, 0, 8) . "\n";
        
        // Update scan with commit SHA
        $scans->update($scanId, ['commit_sha' => $commitSha, 'status' => 'running']);
        
        // Step 2: Run ReDSL scan
        echo "[" . date('Y-m-d H:i:s') . "] Running ReDSL scan...\n";
        
        $artifactsDir = sprintf(
            '%s/var/scans/%s/scan-%d',
            __DIR__ . '/..',
            date('Y/m'),
            $scanId
        );
        
        $runner->scan($clonePath, $artifactsDir);
        
        echo "[" . date('Y-m-d H:i:s') . "] Scan completed. Artifacts: {$artifactsDir}\n";
        
        // Step 3: Parse results
        $scans->updateStatus($scanId, 'parsing');
        
        $metrics = $runner->parseMetrics($artifactsDir);
        $summary = $metrics ?? [
            'files_analyzed' => 0,
            'issues_found' => 0,
            'cc_avg' => 0,
        ];
        
        // Complete scan
        $duration = time() - $startTime;
        $scans->complete($scanId, [
            'artifacts_path' => $artifactsDir,
            'metrics_summary' => json_encode($summary),
            'duration_sec' => $duration,
        ]);
        
        // Update project
        $projects->markScanCompleted($projectId, $commitSha);
        
        echo "[" . date('Y-m-d H:i:s') . "] OK: Scan completed in {$duration}s\n";
        echo "[" . date('Y-m-d H:i:s') . "]    Metrics: " . json_encode($summary) . "\n";
        
        $successCount++;
        
    } catch (Throwable $e) {
        $duration = time() - $startTime;
        $errorMsg = $e->getMessage();
        
        echo "[" . date('Y-m-d H:i:s') . "] FAIL: {$errorMsg}\n";
        
        $scans->fail($scanId, $errorMsg);
        $projects->markError($projectId, $errorMsg);
        
        $failCount++;
    }
    
    // Clear sensitive data from memory
    if (isset($token)) {
        sodium_memzero($token);
    }
}

// Cleanup
flock($lock, LOCK_UN);
fclose($lock);

echo "\n[" . date('Y-m-d H:i:s') . "] Worker done. Success: {$successCount}, Failed: {$failCount}\n";
exit($failCount > 0 ? 1 : 0);
