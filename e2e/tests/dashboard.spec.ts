import { test, expect } from "../fixtures/auth";

test.describe("Dashboard", () => {
  test("displays summary cards reflecting data from modules", async ({
    authenticatedPage: page,
  }) => {
    // Seed data via API first
    const baseURL = page.url().replace(/\/[^/]*$/, "");

    // Create a journal entry (include CSRF header required by backend)
    await page.request.post(`${baseURL}/api/journals`, {
      headers: { "X-Requested-With": "HealthStudio" },
      data: {
        title: "Dashboard Test Journal",
        content: "Testing dashboard summary.",
        entry_date: "2025-06-15",
      },
    });

    // Navigate away and back to force a data refresh
    await page.getByRole("link", { name: "Journal" }).click();
    await page.getByRole("link", { name: "Dashboard" }).click();
    await expect(page.locator("h1")).toContainText("Dashboard");

    // Verify summary section headings exist (use heading role to avoid strict mode)
    await expect(page.getByRole("heading", { name: "Recent Journal Entries" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Active Goals" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Latest Metrics" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Recent PRs" })).toBeVisible();

    // Journal entry should appear
    await expect(page.getByText("Dashboard Test Journal")).toBeVisible();
  });

  test("dashboard links navigate to correct modules", async ({ authenticatedPage: page }) => {
    await page.getByRole("link", { name: "Dashboard" }).click();
    await expect(page.locator("h1")).toContainText("Dashboard");

    // Click on a journal entry link if available
    const journalLink = page.locator("a[href*='/journals/']").first();
    if (await journalLink.isVisible()) {
      await journalLink.click();
      await expect(page.locator("h1")).toContainText("Edit Journal Entry");
      await page.goBack();
    }
  });
});
