// GenesisAI Real-Backend Browser Automation & Screenshot script (CommonJS)
// Connects to local Chrome and takes actual browser screenshots of the running Vite application under USE_MOCK_DATA = false.

const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');
const http = require('http');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const ARTIFACT_DIR = 'C:\\Users\\jishn\\.gemini\\antigravity\\brain\\031ca412-3c7a-4340-b88e-ff0bf4b94ec4';

// Helper to pre-compile a project via backend API so the database has a record on initial page load
function preCompileProject() {
  return new Promise((resolve) => {
    console.log('Sending pre-compilation request to http://localhost:8000/demo/compile...');
    const postData = JSON.stringify({
      prompt: 'Add tiered pricing logic and loyalty discount validators across the Booking ecosystem.',
      execution_mode: 'BALANCED'
    });

    const options = {
      hostname: '127.0.0.1',
      port: 8000,
      path: '/demo/compile',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    };

    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        try {
          const data = JSON.parse(body);
          console.log(`Pre-compilation successful. Generated project_id: ${data.project_id}`);
          resolve(data);
        } catch (e) {
          console.error('Failed to parse pre-compilation response:', body);
          resolve(null);
        }
      });
    });

    req.on('error', (err) => {
      console.error('Pre-compilation network request failed:', err.message);
      resolve(null);
    });

    req.write(postData);
    req.end();
  });
}

// Helper wait function for older puppeteer compatibility
if (!puppeteer.Page.prototype.waitForTimeout) {
  puppeteer.Page.prototype.waitForTimeout = function (timeout) {
    return new Promise(resolve => setTimeout(resolve, timeout));
  };
}

async function run() {
  console.log('Starting screenshot automation script with real backend data...');

  // 1. Pre-compile project
  const preCompiled = await preCompileProject();
  if (!preCompiled) {
    console.warn('Backend server might not be running or failed compilation. Continuing execution anyway...');
  }

  // 2. Launch browser
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  const consoleLogs = [];
  const networkRequests = [];
  const errors = [];

  // Capture Console Logs
  page.on('console', msg => {
    const text = msg.text();
    consoleLogs.push(`[CONSOLE - ${msg.type()}] ${text}`);
    console.log(`[Browser Console] ${text}`);
  });

  // Capture Page Errors
  page.on('pageerror', err => {
    errors.push(err.toString());
    console.error(`[Browser PageError] ${err.toString()}`);
  });

  // Capture responses for detailed network logging (URL, method, status, payload)
  page.on('response', async response => {
    const request = response.request();
    const url = response.url();

    // We only capture API requests sent to localhost:8000
    if (url.includes('localhost:8000') || url.includes('127.0.0.1:8000')) {
      const method = request.method();
      const status = response.status();
      let responsePayload = null;

      if (method !== 'OPTIONS') {
        try {
          responsePayload = await response.json();
        } catch (_) {
          try {
            responsePayload = await response.text();
          } catch (__) {}
        }
      }

      networkRequests.push({
        url,
        method,
        status,
        responsePayload
      });
      console.log(`[Network Log] ${method} ${url} -> ${status}`);
    }
  });

  console.log('Navigating to http://localhost:3000...');
  try {
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle2', timeout: 30000 });
  } catch (err) {
    console.error('Failed to navigate to localhost:3000. Ensure the Vite dev server is running.', err);
    await browser.close();
    process.exit(1);
  }

  await page.waitForTimeout(2000); // Wait for initial loading

  // 1. Click compile button on Dashboard to test /demo/compile request in-browser
  console.log('Clicking the compile button on Dashboard...');
  const clickedCompile = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const target = buttons.find(b => b.textContent.trim() === 'Compile');
    if (target) {
      target.click();
      return true;
    }
    return false;
  });

  if (clickedCompile) {
    console.log('Compile button clicked. Waiting for compilation (4 seconds)...');
    await page.waitForTimeout(4000);
  } else {
    console.warn('Compile button not found on Dashboard page.');
  }

  // 2. Take Compiler Workspace screenshot (since compile routes us here)
  console.log('Capturing Compiler Workspace...');
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'actual_compiler.png') });
  console.log('Compiler Workspace captured.');

  // 3. Go back to Dashboard to take screenshot
  console.log('Navigating to Dashboard tab...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const target = buttons.find(b => b.textContent.includes('Dashboard'));
    if (target) target.click();
  });
  await page.waitForTimeout(2000);
  console.log('Capturing Dashboard...');
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'actual_dashboard.png') });
  console.log('Dashboard captured.');

  // 4. Navigate to Architecture Map
  console.log('Navigating to Architecture tab...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const target = buttons.find(b => b.textContent.includes('Architecture'));
    if (target) target.click();
  });
  await page.waitForTimeout(2000);
  console.log('Capturing Architecture Map...');
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'actual_architecture.png') });
  console.log('Architecture Map captured.');

  // 5. Navigate to Validation
  console.log('Navigating to Validation tab...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const target = buttons.find(b => b.textContent.includes('Validation'));
    if (target) target.click();
  });
  await page.waitForTimeout(2000);
  console.log('Capturing Validation page...');
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'actual_validation.png') });
  console.log('Validation page captured.');

  // 6. Click the INJECT GENESIS_ROLES button to run repair
  console.log('Clicking the INJECT GENESIS_ROLES button to trigger repair...');
  const clickedRepair = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const target = buttons.find(b => b.textContent.includes('INJECT GENESIS_ROLES'));
    if (target) {
      target.click();
      return true;
    }
    return false;
  });

  if (clickedRepair) {
    console.log('Repair button clicked. Waiting for repair re-validation (2 seconds)...');
    await page.waitForTimeout(2000);
  } else {
    console.warn('Repair button not found on Validation page.');
  }
  console.log('Capturing Repair page...');
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'actual_repair.png') });
  console.log('Repair page captured.');

  // 7. Navigate to Simulation
  console.log('Navigating to Simulation tab...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const target = buttons.find(b => b.textContent.includes('Simulation'));
    if (target) target.click();
  });
  await page.waitForTimeout(2000);

  // Click the Run Simulation button
  console.log('Clicking Run Simulation button...');
  const clickedSim = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const target = buttons.find(b => b.textContent.includes('Run Simulation'));
    if (target) {
      target.click();
      return true;
    }
    return false;
  });

  if (clickedSim) {
    console.log('Simulation button clicked. Waiting for run (2 seconds)...');
    await page.waitForTimeout(2000);
  } else {
    console.warn('Run Simulation button not found.');
  }

  console.log('Capturing Simulation Platform...');
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'actual_simulation.png') });
  console.log('Simulation Platform captured.');

  // 8. Navigate to Timeline (Version History)
  console.log('Navigating to Timeline tab...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const target = buttons.find(b => b.textContent.includes('Timeline'));
    if (target) target.click();
  });
  await page.waitForTimeout(2000);
  console.log('Capturing Timeline (Version History)...');
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'actual_timeline.png') });
  console.log('Timeline captured.');

  // Write logs report
  const logReport = {
    consoleLogs,
    networkRequests,
    errors
  };

  fs.writeFileSync(
    path.join(ARTIFACT_DIR, 'browser_execution_logs.json'),
    JSON.stringify(logReport, null, 2)
  );

  console.log('Real backend logs and network requests exported to browser_execution_logs.json');
  await browser.close();
  console.log('Browser screenshots capture complete under USE_MOCK_DATA = false!');
}

run().catch(err => {
  console.error('Fatal error in runner:', err);
  process.exit(1);
});
