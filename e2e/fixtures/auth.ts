import { test as base, type BrowserContext, type Page } from "@playwright/test";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

/**
 * Enable a virtual WebAuthn authenticator on a Chromium page via CDP.
 * Returns the authenticator ID for optional cleanup.
 */
async function addVirtualAuthenticator(page: Page): Promise<string> {
  const client = await page.context().newCDPSession(page);
  await client.send("WebAuthn.enable");
  const { authenticatorId } = await client.send("WebAuthn.addVirtualAuthenticator", {
    options: {
      protocol: "ctap2",
      transport: "internal",
      hasResidentKey: true,
      hasUserVerification: true,
      isUserVerified: true,
    },
  });
  return authenticatorId;
}

/**
 * Reset the application database to a clean state via the test reset endpoint.
 * This clears all user data, sessions, and re-seeds default types.
 */
async function resetApp(): Promise<void> {
  const resp = await fetch(`${API_URL}/api/test/reset`, { method: "POST" });
  if (!resp.ok) {
    throw new Error(`Failed to reset app: ${resp.status} ${resp.statusText}`);
  }
}

/**
 * Register and log in via the UI using a virtual authenticator.
 * Resets the DB first so each test starts fresh.
 */
async function registerAndLogin(page: Page): Promise<void> {
  await resetApp();
  await addVirtualAuthenticator(page);
  await page.goto("/");

  // Should see registration screen on fresh DB
  const heading = page.locator("h1");
  await heading.waitFor({ timeout: 10000 });

  // Registration screen
  await page.locator("h1").filter({ hasText: "Welcome to Health Studio" }).waitFor({ timeout: 10000 });
  const nameInput = page.locator("#displayName");
  await nameInput.clear();
  await nameInput.fill("E2E Test User");
  await page.getByRole("button", { name: "Register with Passkey" }).click();

  // After registration, app reloads to login screen
  await page.locator("h1").filter({ hasText: /^Health Studio$/ }).waitFor({ timeout: 15000 });

  // Login screen
  await page.getByRole("button", { name: "Sign in with Passkey" }).click();
  // Wait for the dashboard to load
  await page.locator("h1").filter({ hasText: "Dashboard" }).waitFor({ timeout: 15000 });
}

/**
 * Seed test data via the API. Requires an authenticated session cookie.
 */
async function seedTestData(context: BrowserContext): Promise<void> {
  const baseURL = process.env.BASE_URL ?? "http://localhost:3000";

  // Create a journal entry
  await context.request.post(`${baseURL}/api/journals`, {
    headers: { "X-Requested-With": "HealthStudio" },
    data: {
      title: "Seed Journal Entry",
      content: "This is a seeded journal entry for testing.",
      entry_date: "2025-01-15",
    },
  });

  // Create a metric entry (use "Weight" type - should exist from DB seed)
  const metricTypesResp = await context.request.get(`${baseURL}/api/metric-types`);
  const metricTypes = await metricTypesResp.json();
  const weightType = metricTypes.find((t: { name: string }) => t.name === "Weight");
  if (weightType) {
    await context.request.post(`${baseURL}/api/metrics`, {
      headers: { "X-Requested-With": "HealthStudio" },
      data: {
        metric_type_id: weightType.id,
        value: 180.5,
        recorded_date: "2025-01-15",
        notes: "Seed metric entry",
      },
    });
  }

  // Create a result entry (use "Back Squat" - should exist from DB seed)
  const exerciseTypesResp = await context.request.get(`${baseURL}/api/exercise-types`);
  const exerciseTypes = await exerciseTypesResp.json();
  const squat = exerciseTypes.find((t: { name: string }) => t.name === "Back Squat");
  if (squat) {
    await context.request.post(`${baseURL}/api/results`, {
      headers: { "X-Requested-With": "HealthStudio" },
      data: {
        exercise_type_id: squat.id,
        value: 315,
        recorded_date: "2025-01-15",
        notes: "Seed result entry",
      },
    });
  }
}

export { addVirtualAuthenticator, registerAndLogin, resetApp, seedTestData };

/**
 * Extended test fixture with authenticated page.
 */
export const test = base.extend<{ authenticatedPage: Page }>({
  authenticatedPage: async ({ page }, use) => {
    await registerAndLogin(page);
    await use(page);
  },
});

export { expect } from "@playwright/test";
