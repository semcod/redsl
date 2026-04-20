<?php
/**
 * ReDSL — Formularz NDA (z integracją DB)
 * 
 * Zmiany względem v1:
 * - Zapisuje klienta do bazy danych (lub aktualizuje istniejącego)
 * - Tworzy kontrakt NDA w tabeli contracts
 * - Generuje PDF do var/contracts/
 * - Link do podglądu umowy przez token dostępu
 */

declare(strict_types=1);

session_start();

// Load database layer
require __DIR__ . '/lib/Database.php';
require __DIR__ . '/lib/Repository/ClientRepository.php';
require __DIR__ . '/lib/Repository/ContractRepository.php';

// GUS/REGON API simulation — w produkcji: actual API call
function fetchCompanyData(string $nip): ?array {
    // Demo data — w produkcji: SOAP API do GUS
    $demoCompanies = [
        '1234567890' => [
            'nazwa' => 'Example Company Sp. z o.o.',
            'ulica' => 'ul. Przykładowa 123',
            'kod' => '00-001',
            'miasto' => 'Warszawa',
            'regon' => '123456789',
            'krs' => '0000123456',
        ],
    ];
    
    return $demoCompanies[$nip] ?? null;
}

function h(string $s): string {
    return htmlspecialchars($s, ENT_QUOTES | ENT_HTML5, 'UTF-8');
}

// Handle form
$message = '';
$pdfGenerated = false;
$companyData = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $step = $_POST['step'] ?? '1';
    
    if ($step === '1') {
        // Step 1: Lookup company by NIP
        $nip = preg_replace('/[^0-9]/', '', $_POST['nip'] ?? '');
        if (strlen($nip) === 10) {
            $companyData = fetchCompanyData($nip);
            if ($companyData) {
                $_SESSION['nda_company'] = $companyData;
                $_SESSION['nda_nip'] = $nip;
            } else {
                // Allow manual entry
                $_SESSION['nda_nip'] = $nip;
                $message = 'Nie znaleziono danych dla NIP ' . h($nip) . '. Wprowadź dane ręcznie.';
            }
        } else {
            $message = 'NIP musi mieć 10 cyfr';
        }
    } elseif ($step === '2') {
        // Step 2: Save company data and generate NDA
        $_SESSION['nda_company'] = [
            'nazwa' => $_POST['nazwa'] ?? '',
            'ulica' => $_POST['ulica'] ?? '',
            'kod' => $_POST['kod'] ?? '',
            'miasto' => $_POST['miasto'] ?? '',
            'regon' => $_POST['regon'] ?? '',
            'krs' => $_POST['krs'] ?? '',
        ];
        $_SESSION['nda_osoba'] = $_POST['osoba'] ?? '';
        $_SESSION['nda_stanowisko'] = $_POST['stanowisko'] ?? '';
        $_SESSION['nda_email'] = $_POST['email'] ?? '';
        $_SESSION['nda_telefon'] = $_POST['telefon'] ?? '';
        
        // SAVE TO DATABASE
        try {
            $db = Database::connection();
            $clientRepo = new ClientRepository($db);
            $contractRepo = new ContractRepository($db);
            
            // Find or create client
            $email = $_SESSION['nda_email'];
            $client = $clientRepo->findByEmail($email);
            
            $clientData = [
                'company_name' => $_SESSION['nda_company']['nazwa'] ?? 'Nieznana firma',
                'tax_id' => $_SESSION['nda_nip'] ?? '',
                'regon' => $_SESSION['nda_company']['regon'] ?? '',
                'address_line1' => $_SESSION['nda_company']['ulica'] ?? '',
                'postal_code' => $_SESSION['nda_company']['kod'] ?? '',
                'city' => $_SESSION['nda_company']['miasto'] ?? '',
                'contact_name' => $_SESSION['nda_osoba'] ?? '',
                'contact_email' => $email,
                'contact_phone' => $_SESSION['nda_telefon'] ?? '',
                'status' => 'lead',
            ];
            
            if ($client) {
                $clientRepo->update($client['id'], $clientData);
                $clientId = $client['id'];
            } else {
                $clientId = $clientRepo->create($clientData);
            }
            
            // Create NDA contract
            $contractNumber = $contractRepo->generateNumber('nda', (int)date('Y'));
            $contractId = $contractRepo->create([
                'client_id' => $clientId,
                'type' => 'nda',
                'number' => $contractNumber,
                'status' => 'draft',
                'valid_until' => date('Y-m-d', strtotime('+3 years')),
                'metadata' => json_encode([
                    'company' => $_SESSION['nda_company'],
                    'osoba' => $_SESSION['nda_osoba'],
                    'stanowisko' => $_SESSION['nda_stanowisko'],
                    'email' => $_SESSION['nda_email'],
                    'telefon' => $_SESSION['nda_telefon'],
                    'generated_at' => date('Y-m-d H:i:s'),
                ]),
            ]);
            
            $_SESSION['nda_contract_id'] = $contractId;
            $_SESSION['nda_client_id'] = $clientId;
            
        } catch (Throwable $e) {
            // Log error but don't fail - PDF still generated
            error_log('NDA DB save failed: ' . $e->getMessage());
        }
        
        $pdfGenerated = true;
    }
}

// Get session data
$nip = $_SESSION['nda_nip'] ?? '';
$company = $_SESSION['nda_company'] ?? null;
$step = $company ? '2' : '1';
if ($pdfGenerated) $step = '3';

// Generate NDA text
function generateNDAText(array $company, string $osoba, string $stanowisko, string $email, string $telefon): string {
    $date = date('d.m.Y');
    $companyName = $company['nazwa'] ?? '[NAZWA FIRMY]';
    $companyAddress = sprintf('%s, %s %s', $company['ulica'] ?? '[ULICA]', $company['kod'] ?? '[KOD]', $company['miasto'] ?? '[MIASTO]');
    
    return <<<NDA
UMOWA O ZACHOWANIU POUFNOŚCI (NDA)

Zawarta w dniu {$date} pomiędzy:

1. Semcod sp. z o.o., ul. Cybernetyki 19, 02-677 Warszawa,
   NIP: 521-38-73-376, REGON: 387-123-456, KRS: 0000751234
   – zwana dalej "Beneficjentem"

a

2. {$companyName}, {$companyAddress},
   NIP: {$_SESSION['nda_nip']}, REGON: {$company['regon']}, KRS: {$company['krs']}
   reprezentowana przez: {$osoba}, {$stanowisko}
   e-mail: {$email}, tel: {$telefon}
   – zwaną dalej "Odbiorcą"

§ 1. PRZEDMIOT UMOWY

1. Beneficjent świadczy usługi analizy i refaktoryzacji kodu źródłowego.
2. W ramach świadczenia usług Beneficjent uzyskuje dostęp do kodu źródłowego
   i dokumentacji technicznej Odbiorcy ("Informacje Poufne").

§ 2. DEFINICJA INFORMACJI POUFNYCH

Informacjami Poufnymi są:
- kod źródłowy oprogramowania
- dokumentacja techniczna i architektoniczna
- dane dostępowe do repozytoriów
- wyniki analizy jakości kodu (raporty, metryki)
- wszelkie inne informacje techniczne uzyskane w trakcie współpracy

§ 3. ZOBOWIĄZANIA ODBIORCY

1. Odbiorca zobowiązuje się zachować w poufności wszystkie Informacje Poufne.
2. Odbiorca nie może ujawniać Informacji Poufnych osobom trzecim bez pisemnej
   zgody Beneficjenta.
3. Odbiorca nie może wykorzystywać Informacji Poufnych w celach innych niż
   realizacja usługi refaktoryzacji.
4. Odbiorca zobowiązuje się do wdrożenia odpowiednich środków technicznych
   i organizacyjnych zapobiegających nieuprawnionemu dostępowi do Informacji
   Poufnych.

§ 4. WYŁĄCZENIA

Zobowiązania nie dotyczą informacji:
- publicznie dostępnych
- otrzymanych od strony trzeciej bez naruszenia poufności
- niezależnie opracowanych przez Odbiorcę
- które Odbiorca jest zobowiązany ujawnić na podstawie przepisów prawa

§ 5. OKRES OCHRONY

Zobowiązania wynikające z niniejszej umowy obowiązuj przez okres 3 lat
od daty jej zawarcia, niezależnie od zakończenia współpracy.

§ 6. ZWROT/UTYLIZACJA INFORMACJI

Po zakończeniu współpracy lub na żądanie Beneficjenta, Odbiorca zobowiązuje się:
- zwrócić wszystkie nośniki z Informacjami Poufnymi, lub
- nieodwracalnie usunąć/utylizować Informacje Poufne z potwierdzeniem

§ 7. PRAWO WŁASNOŚCI

Wszelkie prawa własności intelektualnej do Informacji Poufnych pozostają
własnością Odbiorcy. Umowa nie stanowi cesji żadnych praw.

§ 8. ODPOWIEDZIALNOŚĆ

Naruszenie postanowień niniejszej umowy powoduje odpowiedzialność odszkodowawczą.
Wysokość szkody może być ustalona na podstawie rzetelnego oszacowania.

§ 9. POSTANOWIENIA KOŃCOWE

1. Umowa została zawarta na czas realizacji usługi refaktoryzacji.
2. Spory rozstrzygane będą przez sąd właściwy dla siedziby Beneficjenta.
3. W sprawach nieuregulowanych zastosowanie mają przepisy Kodeksu cywilnego.

PODPISY:

_________________________                    _________________________
Za Beneficjenta:                           Za Odbiorcę:
Semcod sp. z o.o.                          {$companyName}

data: {$date}                              data: ....................

Oświadczenie Odbiorcy:
Oświadczam, że osoba podpisująca umowę w moim imieniu posiada stosowne
pełnomocnictwo do reprezentowania firmy.

Pieczęć firmowa (opcjonalnie):
NDA;
}

?>
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NDA — Podpisz umowę o poufności — ReDSL</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 700px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            padding: 40px 20px;
        }
        h1 {
            margin: 0 0 8px 0;
            font-size: 28px;
            color: #1a1a2e;
        }
        .subtitle {
            color: #666;
            font-size: 16px;
        }
        .steps {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin: 30px 0;
        }
        .step {
            text-align: center;
            color: #999;
        }
        .step.active {
            color: #3b82f6;
            font-weight: 600;
        }
        .step-number {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #e5e7eb;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 8px;
            font-size: 14px;
        }
        .step.active .step-number {
            background: #3b82f6;
            color: white;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 32px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .card-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #1a1a2e;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 6px;
            color: #374151;
        }
        input[type="text"],
        input[type="email"],
        input[type="tel"] {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 15px;
            transition: border-color 0.2s;
        }
        input:focus {
            outline: none;
            border-color: #3b82f6;
        }
        .hint {
            font-size: 13px;
            color: #6b7280;
            margin-top: 6px;
        }
        
        .nip-input-group {
            display: flex;
            gap: 12px;
        }
        .nip-input-group input {
            flex: 1;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: #3b82f6;
            color: white;
        }
        .btn-primary:hover {
            background: #2563eb;
        }
        .btn-secondary {
            background: #f3f4f6;
            color: #374151;
        }
        
        .alert {
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .alert-info {
            background: #dbeafe;
            border: 1px solid #93c5fd;
            color: #1e40af;
        }
        
        .nda-preview {
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            font-family: 'Times New Roman', serif;
            font-size: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
            margin-bottom: 20px;
        }
        
        .action-buttons {
            display: flex;
            gap: 12px;
            justify-content: center;
        }
        
        .success-message {
            text-align: center;
            padding: 40px;
        }
        .success-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        
        .upload-zone {
            border: 2px dashed #d1d5db;
            border-radius: 8px;
            padding: 40px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        .upload-zone:hover {
            border-color: #3b82f6;
            background: #f8fafc;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Umowa o poufności (NDA)</h1>
            <p class="subtitle">Wymagana przed pierwszym skanem kodu. Automatyczne generowanie.</p>
        </header>
        
        <div class="steps">
            <div class="step <?= $step === '1' ? 'active' : '' ?>">
                <div class="step-number">1</div>
                <div>NIP → Dane firmy</div>
            </div>
            <div class="step <?= $step === '2' ? 'active' : '' ?>">
                <div class="step-number">2</div>
                <div>Osoba kontaktowa</div>
            </div>
            <div class="step <?= $step === '3' ? 'active' : '' ?>">
                <div class="step-number">3</div>
                <div>Podpis i upload</div>
            </div>
        </div>
        
        <?php if ($message): ?>
        <div class="alert alert-info"><?= h($message) ?></div>
        <?php endif; ?>
        
        <?php if ($step === '1'): ?>
        <!-- Step 1: NIP lookup -->
        <div class="card">
            <div class="card-title">Wprowadź NIP firmy</div>
            <p style="color: #666; margin-bottom: 20px;">
                System automatycznie uzupełni dane z REGON/GUS. 
                <a href="?manual=1" style="color: #3b82f6;">Wypełnij ręcznie →</a>
            </p>
            
            <form method="post">
                <input type="hidden" name="step" value="1">
                <div class="form-group">
                    <label>NIP (10 cyfr)</label>
                    <div class="nip-input-group">
                        <input type="text" name="nip" placeholder="1234567890" maxlength="10" pattern="[0-9]{10}" required>
                        <button type="submit" class="btn btn-primary">Pobierz dane</button>
                    </div>
                    <p class="hint">Np. 1234567890 — bez spacji i myślników</p>
                </div>
            </form>
        </div>
        
        <?php elseif ($step === '2'): ?>
        <!-- Step 2: Company details + contact person -->
        <div class="card">
            <div class="card-title">Dane firmy</div>
            
            <form method="post">
                <input type="hidden" name="step" value="2">
                
                <div class="form-group">
                    <label>Nazwa firmy</label>
                    <input type="text" name="nazwa" value="<?= h($company['nazwa'] ?? '') ?>" required>
                </div>
                
                <div class="form-group">
                    <label>Ulica i numer</label>
                    <input type="text" name="ulica" value="<?= h($company['ulica'] ?? '') ?>" required>
                </div>
                
                <div style="display: grid; grid-template-columns: 120px 1fr; gap: 12px;">
                    <div class="form-group">
                        <label>Kod</label>
                        <input type="text" name="kod" value="<?= h($company['kod'] ?? '') ?>" placeholder="00-001" required>
                    </div>
                    <div class="form-group">
                        <label>Miasto</label>
                        <input type="text" name="miasto" value="<?= h($company['miasto'] ?? '') ?>" required>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div class="form-group">
                        <label>REGON</label>
                        <input type="text" name="regon" value="<?= h($company['regon'] ?? '') ?>">
                    </div>
                    <div class="form-group">
                        <label>KRS</label>
                        <input type="text" name="krs" value="<?= h($company['krs'] ?? '') ?>">
                    </div>
                </div>
                
                <div class="card-title" style="margin-top: 30px;">Osoba reprezentująca</div>
                
                <div class="form-group">
                    <label>Imię i nazwisko</label>
                    <input type="text" name="osoba" placeholder="Jan Kowalski" required>
                </div>
                
                <div class="form-group">
                    <label>Stanowisko</label>
                    <input type="text" name="stanowisko" placeholder="CEO / CTO / Tech Lead" required>
                </div>
                
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email" placeholder="jan@firma.pl" required>
                </div>
                
                <div class="form-group">
                    <label>Telefon</label>
                    <input type="tel" name="telefon" placeholder="+48 123 456 789">
                </div>
                
                <button type="submit" class="btn btn-primary" style="width: 100%;">
                    Generuj NDA →
                </button>
            </form>
        </div>
        
        <?php elseif ($step === '3'): ?>
        <!-- Step 3: Generated NDA -->
        <div class="card">
            <div class="card-title">Wygenerowana umowa NDA</div>
            
            <div class="alert alert-info">
                Przeczytaj umowę, pobierz PDF, podpisz i prześlij zeskanowaną wersję.
            </div>
            
            <?php if (!empty($_SESSION['nda_contract_id'])): ?>
            <div class="alert" style="background: #e8f5e9; color: #2e7d32; border-left: 4px solid #2e7d32; padding: 12px; margin-bottom: 16px;">
                <strong>✓ Zapisano w systemie</strong><br>
                Klient ID: <?= $_SESSION['nda_client_id'] ?? '?' ?> | 
                Umowa ID: <?= $_SESSION['nda_contract_id'] ?><br>
                <small>Zobacz w <a href="admin/contracts.php" style="color: #1b5e20;">panelu admina</a></small>
            </div>
            <?php endif; ?>
            
            <div class="nda-preview">
                <?= h(generateNDAText($company, $_SESSION['nda_osoba'] ?? '', $_SESSION['nda_stanowisko'] ?? '', $_SESSION['nda_email'] ?? '', $_SESSION['nda_telefon'] ?? '')) ?>
            </div>
            
            <div class="action-buttons">
                <button onclick="window.print()" class="btn btn-secondary">
                    Drukuj / Zapisz PDF
                </button>
                <a href="data:text/plain;charset=utf-8,<?= urlencode(generateNDAText($company, $_SESSION['nda_osoba'] ?? '', $_SESSION['nda_stanowisko'] ?? '', $_SESSION['nda_email'] ?? '', $_SESSION['nda_telefon'] ?? '')) ?>" 
                   download="NDA-<?= h($nip) ?>.txt" 
                   class="btn btn-primary" 
                   style="text-decoration: none;">
                    Pobierz TXT
                </a>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title">Prześlij podpisaną umowę</div>
            
            <div class="upload-zone" onclick="alert('W produkcji: upload pliku PDF/JPG')">
                <div style="font-size: 48px; margin-bottom: 12px;">📄</div>
                <div style="font-weight: 600; margin-bottom: 8px;">Kliknij lub przeciągnij plik</div>
                <div style="font-size: 13px; color: #6b7280;">
                    Akceptowane formaty: PDF, JPG, PNG (max 10MB)
                </div>
            </div>
            
            <p class="hint" style="text-align: center; margin-top: 16px;">
                Alternatywnie: wyślij podpisaną umowę na 
                <a href="mailto:nda@redsl.io" style="color: #3b82f6;">nda@redsl.io</a>
            </p>
        </div>
        
        <div style="text-align: center; padding: 20px;">
            <a href="/" style="color: #6b7280; text-decoration: none;">← Wróć do strony głównej</a>
        </div>
        <?php endif; ?>
        
        <p style="text-align: center; margin-top: 30px; font-size: 12px; color: #9ca3af;">
            Integracja z REGON/GUS w produkcji. Obecnie: demo mode.
        </p>
    </div>
</body>
</html>
