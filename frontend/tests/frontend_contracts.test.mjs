import { test } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test('Frontend production build bundle exists and is valid', () => {
  const distHtmlPath = path.join(__dirname, '..', 'dist', 'index.html');
  assert.ok(fs.existsSync(distHtmlPath), 'dist/index.html should exist');
  
  const content = fs.readFileSync(distHtmlPath, 'utf-8');
  assert.ok(content.includes('Amulate AI | Car Rental & Purchase Consultant'), 'Title should be present');
  assert.ok(content.includes('assets/'), 'Bundle script should be referenced');
});

test('Booking MCP App file exists and contains valid lifecycle hooks', () => {
  const bookingAppPath = path.join(__dirname, '..', '..', 'mcp-apps', 'booking', 'index.html');
  assert.ok(fs.existsSync(bookingAppPath), 'mcp-apps/booking/index.html should exist');

  const content = fs.readFileSync(bookingAppPath, 'utf-8');
  assert.ok(content.includes('mcp-app:init'), 'Must handle mcp-app:init');
  assert.ok(content.includes('mcp-app:ready'), 'Must emit mcp-app:ready');
  assert.ok(content.includes('mcp-app:action'), 'Must handle mcp-app:action');
  assert.ok(content.includes('mcp-app:finish'), 'Must emit mcp-app:finish');
  assert.ok(content.includes('recalculate'), 'Must support recalculation action');
});

test('Mock Checkout MCP App file exists and contains safety disclaimers', () => {
  const checkoutAppPath = path.join(__dirname, '..', '..', 'mcp-apps', 'checkout', 'index.html');
  assert.ok(fs.existsSync(checkoutAppPath), 'mcp-apps/checkout/index.html should exist');

  const content = fs.readFileSync(checkoutAppPath, 'utf-8');
  assert.ok(content.includes('mcp-app:init'), 'Must handle mcp-app:init');
  assert.ok(content.includes('mcp-app:finish'), 'Must emit mcp-app:finish');
  assert.ok(content.includes('MOCK PAYMENT SIMULATOR'), 'Must show mock payment disclaimer');
  assert.ok(content.includes('Instant Success'), 'Must support Instant Success scenario');
  assert.ok(content.includes('Simulated Decline'), 'Must support Simulated Decline scenario');
});

test('A2UI protocol component catalog integrity', () => {
  const a2uiPath = path.join(__dirname, '..', 'src', 'a2ui', 'A2UIRenderer.tsx');
  assert.ok(fs.existsSync(a2uiPath), 'A2UIRenderer.tsx must exist');

  const content = fs.readFileSync(a2uiPath, 'utf-8');
  assert.ok(content.includes('VehicleCard'), 'Must support VehicleCard component');
  assert.ok(content.includes('RadioGroup'), 'Must support RadioGroup component');
  assert.ok(content.includes('Card'), 'Must support Card component');
  assert.ok(content.includes('Grid'), 'Must support Grid component');
  assert.ok(content.includes('Button'), 'Must support Button component');
  assert.ok(content.includes('positiveMatches'), 'Must render positive matches');
  assert.ok(content.includes('tradeOffs'), 'Must render trade offs');
});

