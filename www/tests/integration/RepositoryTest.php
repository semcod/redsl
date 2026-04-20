<?php
/**
 * Integration Tests for REDSL Repositories
 * 
 * Tests: ClientRepository, ProjectRepository, ContractRepository, etc.
 * Requires: MySQL database with test schema
 */

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

require __DIR__ . '/../../lib/Database.php';
require __DIR__ . '/../../lib/Repository/ClientRepository.php';
require __DIR__ . '/../../lib/Repository/ProjectRepository.php';
require __DIR__ . '/../../lib/Repository/ContractRepository.php';

/**
 * @group integration
 * @group database
 */
class RepositoryTest extends TestCase
{
    private static ?PDO $db = null;
    private ClientRepository $clients;
    private ProjectRepository $projects;
    private ContractRepository $contracts;
    
    public static function setUpBeforeClass(): void
    {
        // Use test database if available, otherwise skip
        try {
            putenv('DB_HOST=localhost');
            putenv('DB_NAME=redsl_test');
            putenv('DB_USER=root');
            putenv('DB_PASS=');
            
            self::$db = Database::connection();
            
            // Clear test data
            self::$db->exec("DELETE FROM tickets");
            self::$db->exec("DELETE FROM invoice_items");
            self::$db->exec("DELETE FROM invoices");
            self::$db->exec("DELETE FROM contracts");
            self::$db->exec("DELETE FROM scan_runs");
            self::$db->exec("DELETE FROM projects");
            self::$db->exec("DELETE FROM clients");
            
        } catch (Exception $e) {
            self::markTestSkipped('Database not available: ' . $e->getMessage());
        }
    }
    
    protected function setUp(): void
    {
        if (!self::$db) {
            $this->markTestSkipped('Database not available');
        }
        
        $this->clients = new ClientRepository(self::$db);
        $this->projects = new ProjectRepository(self::$db);
        $this->contracts = new ContractRepository(self::$db);
    }
    
    /**
     * @test
     */
    public function testClientLifecycle(): void
    {
        // Create
        $clientId = $this->clients->create([
            'company_name' => 'Test Company Sp. z o.o.',
            'tax_id' => '1234567890',
            'contact_name' => 'Jan Testowy',
            'contact_email' => 'test@example.com',
            'contact_phone' => '+48 123 456 789',
            'status' => 'lead',
        ]);
        
        $this->assertGreaterThan(0, $clientId);
        
        // Read
        $client = $this->clients->find($clientId);
        $this->assertNotNull($client);
        $this->assertEquals('Test Company Sp. z o.o.', $client['company_name']);
        $this->assertEquals('test@example.com', $client['contact_email']);
        
        // Find by email
        $found = $this->clients->findByEmail('test@example.com');
        $this->assertNotNull($found);
        $this->assertEquals($clientId, $found['id']);
        
        // Update
        $result = $this->clients->update($clientId, [
            'company_name' => 'Updated Company',
            'status' => 'active',
        ]);
        $this->assertTrue($result);
        
        $updated = $this->clients->find($clientId);
        $this->assertEquals('Updated Company', $updated['company_name']);
        $this->assertEquals('active', $updated['status']);
        
        // Search
        $results = $this->clients->search('Updated');
        $this->assertCount(1, $results);
        
        // Archive (soft delete)
        $result = $this->clients->archive($clientId);
        $this->assertTrue($result);
        
        $archived = $this->clients->find($clientId);
        $this->assertEquals('archived', $archived['status']);
    }
    
    /**
     * @test
     */
    public function testProjectLifecycle(): void
    {
        // Create client first
        $clientId = $this->clients->create([
            'company_name' => 'Project Test Company',
            'contact_email' => 'project@example.com',
            'status' => 'active',
        ]);
        
        // Create project
        $projectId = $this->projects->create([
            'client_id' => $clientId,
            'name' => 'Test Project',
            'repo_url' => 'https://github.com/test/repo',
            'repo_provider' => 'github',
            'default_branch' => 'main',
            'scan_schedule' => 'weekly',
            'status' => 'active',
        ]);
        
        $this->assertGreaterThan(0, $projectId);
        
        // Read
        $project = $this->projects->find($projectId);
        $this->assertNotNull($project);
        $this->assertEquals('Test Project', $project['name']);
        
        // Find by client
        $byClient = $this->projects->findByClient($clientId);
        $this->assertCount(1, $byClient);
        
        // Mark scan completed
        $result = $this->projects->markScanCompleted($projectId, 'abc123def456');
        $this->assertTrue($result);
        
        $completed = $this->projects->find($projectId);
        $this->assertEquals('abc123def456', $completed['last_commit_sha']);
        $this->assertNotNull($completed['last_scan_at']);
        
        // Mark error
        $result = $this->projects->markError($projectId, 'Connection timeout');
        $this->assertTrue($result);
        
        $errored = $this->projects->find($projectId);
        $this->assertEquals('error', $errored['status']);
        $this->assertEquals('Connection timeout', $errored['last_error']);
    }
    
    /**
     * @test
     */
    public function testContractLifecycle(): void
    {
        // Create client
        $clientId = $this->clients->create([
            'company_name' => 'Contract Test Company',
            'contact_email' => 'contract@example.com',
            'status' => 'active',
        ]);
        
        // Create contract
        $contractId = $this->contracts->create([
            'client_id' => $clientId,
            'type' => 'nda',
            'number' => 'NDA/2026/001',
            'status' => 'draft',
            'valid_until' => '2029-12-31',
        ]);
        
        $this->assertGreaterThan(0, $contractId);
        
        // Mark as sent
        $result = $this->contracts->markSent($contractId, 'var/contracts/test.pdf');
        $this->assertTrue($result);
        
        $sent = $this->contracts->find($contractId);
        $this->assertEquals('sent', $sent['status']);
        $this->assertNotNull($sent['sent_at']);
        $this->assertNotNull($sent['access_token']);
        
        // Mark as signed
        $result = $this->contracts->markSigned($contractId, 'var/contracts/signed.pdf');
        $this->assertTrue($result);
        
        $signed = $this->contracts->find($contractId);
        $this->assertEquals('signed', $signed['status']);
        $this->assertNotNull($signed['signed_at']);
    }
    
    /**
     * @test
     */
    public function testContractNumberGeneration(): void
    {
        // Create client
        $clientId = $this->clients->create([
            'company_name' => 'Number Gen Company',
            'contact_email' => 'numbers@example.com',
            'status' => 'active',
        ]);
        
        // Create first contract
        $num1 = $this->contracts->generateNumber('nda', 2026);
        $this->assertStringContainsString('NDA/2026/', $num1);
        
        $this->contracts->create([
            'client_id' => $clientId,
            'type' => 'nda',
            'number' => $num1,
            'status' => 'draft',
        ]);
        
        // Second contract should have different number
        $num2 = $this->contracts->generateNumber('nda', 2026);
        $this->assertNotEquals($num1, $num2);
    }
    
    /**
     * @test
     */
    public function testClientCountByStatus(): void
    {
        // Create clients with different statuses
        $this->clients->create([
            'company_name' => 'Active 1',
            'contact_email' => 'a1@example.com',
            'status' => 'active',
        ]);
        
        $this->clients->create([
            'company_name' => 'Active 2',
            'contact_email' => 'a2@example.com',
            'status' => 'active',
        ]);
        
        $this->clients->create([
            'company_name' => 'Lead 1',
            'contact_email' => 'l1@example.com',
            'status' => 'lead',
        ]);
        
        $counts = $this->clients->countByStatus();
        $this->assertArrayHasKey('active', $counts);
        $this->assertArrayHasKey('lead', $counts);
        $this->assertGreaterThanOrEqual(2, $counts['active']);
        $this->assertGreaterThanOrEqual(1, $counts['lead']);
    }
}
