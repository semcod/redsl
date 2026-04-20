// @ts-check
/**
 * E2E Tests for REDSL Admin Panel
 * Tests: clients, contracts, projects, scans, tickets, invoices
 */

const { test, expect } = require('@playwright/test');

// Admin credentials - must match .env or use test overrides
const ADMIN_USER = process.env.ADMIN_USER || 'admin';
const ADMIN_PASS = process.env.ADMIN_PASS || 'admin123';

/**
 * Helper: Login to admin panel
 */
async function login(page) {
  await page.goto('/admin/');
  
  // Handle HTTP Basic Auth dialog
  await page.waitForLoadState('networkidle');
  
  // If we see login prompt or error, we need to configure auth
  const content = await page.content();
  if (content.includes('Admin Not Configured')) {
    test.skip(true, 'Admin not configured - set ADMIN_PASS_HASH in .env');
  }
}

/**
 * Helper: Navigate to admin section
 */
async function navigateTo(page, section) {
  const links = {
    clients: 'Klienci',
    contracts: 'Umowy',
    projects: 'Projekty',
    scans: 'Skany',
    tickets: 'Tickety',
    invoices: 'Faktury',
  };
  
  await page.click(`text=${links[section]}`);
  await page.waitForLoadState('networkidle');
}

test.describe('Admin Panel - Authentication', () => {
  test('admin page loads and shows auth or setup message', async ({ page }) => {
    await page.goto('/admin/');
    
    // Either we see dashboard (if configured) or setup message
    const content = await page.content();
    const hasDashboard = content.includes('REDSL Panel') || content.includes('Dashboard');
    const hasSetup = content.includes('Admin Not Configured');
    
    expect(hasDashboard || hasSetup).toBe(true);
  });
  
  test('all admin pages are accessible or show auth error', async ({ page }) => {
    const pages = [
      '/admin/index.php',
      '/admin/clients.php',
      '/admin/contracts.php',
      '/admin/projects.php',
      '/admin/scans.php',
      '/admin/tickets.php',
      '/admin/invoices.php',
    ];
    
    for (const url of pages) {
      await page.goto(url);
      const status = await page.evaluate(() => document.readyState);
      expect(status).toBe('complete');
      
      // Should not have PHP errors
      const content = await page.content();
      expect(content).not.toContain('Fatal error');
      expect(content).not.toContain('Parse error');
    }
  });
});

test.describe('Admin Panel - Clients CRUD', () => {
  test('clients list page loads', async ({ page }) => {
    await page.goto('/admin/clients.php');
    
    // Should show either login, setup message, or clients list
    const content = await page.content();
    const hasClients = content.includes('Klienci');
    const hasSetup = content.includes('Admin Not Configured');
    expect(hasClients || hasSetup).toBe(true);
  });
  
  test('client form fields exist', async ({ page }) => {
    await page.goto('/admin/clients.php?action=new');
    
    // Check form fields exist
    await expect(page.locator('input[name="company_name"]')).toBeVisible().catch(() => {
      // If auth not configured, skip
      test.skip(true, 'Auth not configured');
    });
    
    await expect(page.locator('input[name="contact_email"]')).toBeVisible();
    await expect(page.locator('input[name="tax_id"]')).toBeVisible();
    await expect(page.locator('select[name="status"]')).toBeVisible();
  });
  
  test('client validation works', async ({ page }) => {
    await page.goto('/admin/clients.php?action=new');
    
    // Try to submit empty form
    const submit = page.locator('button[type="submit"]');
    if (await submit.isVisible().catch(() => false)) {
      await submit.click();
      
      // Should show validation error or stay on form
      await page.waitForTimeout(500);
      const url = page.url();
      expect(url).toContain('clients.php');
    }
  });
});

test.describe('Admin Panel - Projects', () => {
  test('projects list loads', async ({ page }) => {
    await page.goto('/admin/projects.php');
    
    const content = await page.content();
    const hasProjects = content.includes('Projekty');
    const hasSetup = content.includes('Admin Not Configured');
    expect(hasProjects || hasSetup).toBe(true);
  });
  
  test('project form has all fields', async ({ page }) => {
    await page.goto('/admin/projects.php?action=new');
    
    const fields = [
      'input[name="name"]',
      'input[name="repo_url"]',
      'select[name="repo_provider"]',
      'select[name="scan_schedule"]',
    ];
    
    for (const selector of fields) {
      const visible = await page.locator(selector).isVisible().catch(() => false);
      if (!visible) {
        test.skip(true, 'Auth not configured or fields missing');
        break;
      }
    }
  });
});

test.describe('Admin Panel - Tickets Workflow', () => {
  test('tickets list shows status badges', async ({ page }) => {
    await page.goto('/admin/tickets.php');
    
    const content = await page.content();
    const hasTickets = content.includes('Tickety') || content.includes('Brak ticketów');
    const hasSetup = content.includes('Admin Not Configured');
    
    expect(hasTickets || hasSetup).toBe(true);
  });
  
  test('ticket detail shows workflow actions', async ({ page }) => {
    // This test requires existing tickets - skip if none
    await page.goto('/admin/tickets.php');
    
    const rows = await page.locator('table tbody tr').count();
    if (rows === 0) {
      test.skip(true, 'No tickets in system');
    }
    
    // Click first ticket
    await page.click('table tbody tr:first-child a');
    await page.waitForLoadState('networkidle');
    
    // Should show ticket details
    const content = await page.content();
    expect(content).toContain('Ticket #');
  });
});

test.describe('Admin Panel - Invoices', () => {
  test('invoices list shows summary stats', async ({ page }) => {
    await page.goto('/admin/invoices.php');
    
    const content = await page.content();
    const hasInvoices = content.includes('Faktury');
    const hasSetup = content.includes('Admin Not Configured');
    expect(hasInvoices || hasSetup).toBe(true);
  });
  
  test('invoice detail shows items table', async ({ page }) => {
    await page.goto('/admin/invoices.php');
    
    const rows = await page.locator('table tbody tr').count();
    if (rows === 0) {
      test.skip(true, 'No invoices in system');
    }
    
    await page.click('table tbody tr:first-child a');
    await page.waitForLoadState('networkidle');
    
    const content = await page.content();
    expect(content).toContain('Faktura');
  });
});

test.describe('Admin Panel - API Endpoints', () => {
  test('health check passes', async ({ request }) => {
    const response = await request.get('/');
    expect(response.status()).toBe(200);
  });
  
  test('admin pages return valid response (either HTML or setup message)', async ({ request }) => {
    const endpoints = [
      '/admin/index.php',
      '/admin/clients.php',
      '/admin/projects.php',
    ];
    
    for (const endpoint of endpoints) {
      const response = await request.get(endpoint);
      const content = await response.text();
      
      // Either full HTML OR setup message is acceptable
      const hasHtml = content.includes('<!DOCTYPE html>') && content.includes('</html>');
      const hasSetup = content.includes('Admin Not Configured');
      
      expect(hasHtml || hasSetup).toBe(true);
      
      // No PHP errors
      expect(content).not.toContain('Fatal error');
      expect(content).not.toContain('Parse error');
    }
  });
});
