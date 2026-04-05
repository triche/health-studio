import { test, expect, addVirtualAuthenticator, resetApp } from "../fixtures/auth";

test.describe("Auth Flow", () => {
  test("shows registration screen on fresh app", async ({ page }) => {
    await resetApp();
    await addVirtualAuthenticator(page);
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("Welcome to Health Studio");
    await expect(page.getByRole("button", { name: "Register with Passkey" })).toBeVisible();
  });

  test("registers a new user and redirects to login", async ({ page }) => {
    await resetApp();
    await addVirtualAuthenticator(page);
    await page.goto("/");

    const nameInput = page.locator("#displayName");
    await nameInput.clear();
    await nameInput.fill("Test User");
    await page.getByRole("button", { name: "Register with Passkey" }).click();

    // Should redirect to login after registration
    await expect(page.locator("h1").filter({ hasText: /^Health Studio$/ })).toBeVisible({
      timeout: 15000,
    });
    await expect(page.getByRole("button", { name: "Sign in with Passkey" })).toBeVisible();
  });

  test("logs in after registration and reaches dashboard", async ({ page }) => {
    await resetApp();
    await addVirtualAuthenticator(page);
    await page.goto("/");

    // Register
    const nameInput = page.locator("#displayName");
    await nameInput.clear();
    await nameInput.fill("Test User");
    await page.getByRole("button", { name: "Register with Passkey" }).click();
    await page.getByRole("button", { name: "Sign in with Passkey" }).waitFor({ timeout: 15000 });

    // Login
    await page.getByRole("button", { name: "Sign in with Passkey" }).click();
    await expect(page.locator("h1").filter({ hasText: "Dashboard" })).toBeVisible({
      timeout: 15000,
    });
  });

  test("logout returns to login screen", async ({ authenticatedPage: page }) => {
    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(page.getByRole("button", { name: "Sign in with Passkey" })).toBeVisible({
      timeout: 10000,
    });
  });
});
