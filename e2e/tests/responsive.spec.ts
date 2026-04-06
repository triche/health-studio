import { test, expect } from "../fixtures/auth";

test.describe("Responsive Layout", () => {
  // This test file runs under the "mobile" project with 375x812 viewport

  test("mobile hamburger menu opens and closes", async ({ authenticatedPage: page }) => {
    // On mobile, the sidebar should be hidden by default
    // The hamburger button should be visible
    await page.getByRole("button", { name: "Open menu" }).click();

    // Sidebar overlay should appear
    await expect(page.locator("[data-testid='sidebar-overlay']")).toBeVisible();

    // Navigation links should be visible
    await expect(page.getByRole("link", { name: "Dashboard" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Journal" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Metrics" })).toBeVisible();

    // Close menu
    await page.getByRole("button", { name: "Close menu" }).click();
    await expect(page.locator("[data-testid='sidebar-overlay']")).not.toBeVisible();
  });

  test("mobile navigation works through hamburger menu", async ({ authenticatedPage: page }) => {
    const pages = [
      { link: "Journal", heading: "Journal" },
      { link: "Metrics", heading: "Metrics" },
      { link: "Results", heading: "Results" },
      { link: "Goals", heading: "Goals" },
    ];

    for (const { link, heading } of pages) {
      await page.getByRole("button", { name: "Open menu" }).click();
      await page.getByRole("link", { name: link }).click();
      await expect(page.locator("h1").first()).toContainText(heading);
    }
  });

  test("journal CRUD works at mobile viewport", async ({ authenticatedPage: page }) => {
    // Open menu and navigate to journals
    await page.getByRole("button", { name: "Open menu" }).click();
    await page.getByRole("link", { name: "Journal" }).click();
    await expect(page.locator("h1")).toContainText("Journal");

    // Create new entry
    await page.getByRole("link", { name: "New Entry" }).click();
    await page.locator("#title").fill("Mobile Test Entry");
    await page.locator("#entry_date").fill("2025-07-01");
    await page.locator(".w-md-editor-text-input").fill("Written on mobile viewport.");
    await page.getByRole("button", { name: "Create" }).click();

    // Verify it appears
    await expect(page.getByText("Mobile Test Entry")).toBeVisible();
  });
});
