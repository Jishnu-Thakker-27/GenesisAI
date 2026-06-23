// GenesisAI Browser Automation & Screenshot script (CommonJS)
// Connects to local Chrome and takes actual browser screenshots of the running Vite application.

const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const ARTIFACT_DIR = 'C:\\Users\\jishn\\.gemini\\antigravity\\brain\\031ca412-3c7a-4340-b88e-ff0bf4b94ec4';

async function run() {
  console.log('Starting screenshot automation script...');
  
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
    consoleLogs.push(`[CONSOLE - ${msg.type()}] ${msg.text()}`);
    console.log(`[Browser Console] ${msg.text()}`);
  });

  // Capture Network Requests
  page.on('request', request => {
    networkRequests.push({
      url: request.url(),
      method: request.method(),
      status: 'PENDING'
    });
  });

  page.on('requestfinished', request => {
    const matched = networkRequests.find(r => r.url === request.url());
    if (matched) {
      const response = request.response();
      matched.status = response ? response.status() : 'SUCCESS';
    }
  });

  page.on('requestfailed', request => {
    const matched = networkRequests.find(r => r.url === request.url());
    if (matched) {
      matched.status = 'FAILED';
    }
  });

  // Capture Page Errors
  page.on('pageerror', err => {
    errors.push(err.toString());
    console.error(`[Browser PageError] ${err.toString()}`);
  });

  console.log('Navigating to http://localhost:3000...');
  try {
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle2', timeout: 30000 });
  } catch (err) {
    console.error('Failed to navigate to localhost:3000. Ensure the Vite dev server is running.', err);
    await browser.close();
    process.exit(1);
  }

  // 1. Dashboard screenshot
  console.log('Capturing Dashboard screen...');
  await page.waitForTimeout(2000); // Wait for initial loading
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'actual_dashboard.png') });
  console.log('Dashboard captured.');

  const screens = [
    { name: 'Compiler', file: 'actual_compiler.png' },
    { name: 'Architecture', file: 'actual_architecture.png' },
    { name: 'Validation', file: 'actual_validation.png' },
    { name: 'Repair', file: 'actual_repair.png' },
    { name: 'Simulation', file: 'actual_simulation.png' },
    { name: 'Timeline', file: 'actual_timeline.png' }
  ];

  for (const screen of screens) {
    console.log(`Navigating to ${screen.name} tab...`);
    
    // Find button containing the name of the tab
    const clicked = await page.evaluate(async (tabName) => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const target = buttons.find(b => b.textContent.includes(tabName));
      if (target) {
        target.click();
        return true;
      }
      return false;
    }, screen.name);

    if (clicked) {
      console.log(`Clicked tab button for ${screen.name}. Waiting for render...`);
      await page.waitForTimeout(1500); // Wait for transitions and mock queries
      await page.screenshot({ path: path.join(ARTIFACT_DIR, screen.file) });
      console.log(`${screen.name} screen captured successfully.`);
    } else {
      console.warn(`Could not find click button for tab: ${screen.name}`);
    }
  }

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

  console.log('Logs and network requests exported to browser_execution_logs.json');
  await browser.close();
  console.log('Browser screenshots capture complete!');
}

// Helper wait function for older puppeteer compatibility
if (!puppeteer.Page.prototype.waitForTimeout) {
  puppeteer.Page.prototype.waitForTimeout = function (timeout) {
    return new Promise(resolve => setTimeout(resolve, timeout));
  };
}

run().catch(err => {
  console.error('Fatal error in runner:', err);
  process.exit(1);
});
