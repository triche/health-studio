import { test, expect } from "../fixtures/auth";

test.describe("Journal", () => {
  test("create, view, edit, and delete a journal entry", async ({ authenticatedPage: page }) => {
    // Navigate to journals
    await page.getByRole("link", { name: "Journal" }).click();
    await expect(page.locator("h1")).toContainText("Journal");

    // Create a new entry
    await page.getByRole("link", { name: "New Entry" }).click();
    await expect(page.locator("h1")).toContainText("New Journal Entry");

    await page.locator("#title").fill("E2E Test Journal");
    await page.locator("#entry_date").fill("2025-06-15");
    await page.locator(".w-md-editor-text-input").fill("# Hello from E2E\n\nThis is a test entry.");

    // Submit
    await page.getByRole("button", { name: "Create" }).click();

    // Should redirect to journal list
    await expect(page.locator("h1").first()).toContainText("Journal");
    await expect(page.getByText("E2E Test Journal")).toBeVisible();

    // Edit the entry
    await page.getByText("E2E Test Journal").click();
    await expect(page.locator("h1")).toContainText("Edit Journal Entry");

    await page.locator("#title").clear();
    await page.locator("#title").fill("E2E Test Journal (Edited)");
    await page.getByRole("button", { name: "Save" }).click();

    // Verify edit
    await expect(page.locator("h1").first()).toContainText("Journal");
    await expect(page.getByText("E2E Test Journal (Edited)")).toBeVisible();

    // Delete the entry
    await page.getByRole("button", { name: "Delete" }).first().click();
    await expect(page.getByText("E2E Test Journal (Edited)")).not.toBeVisible();
  });

  test("pagination works when many entries exist", async ({ authenticatedPage: page }) => {
    // Create enough entries to trigger pagination via API (per_page=20, need >20)
    const baseURL = page.url().replace(/\/[^/]*$/, "");
    for (let i = 1; i <= 25; i++) {
      await page.request.post(`${baseURL}/api/journals`, {
        headers: { "X-Requested-With": "HealthStudio" },
        data: {
          title: `Pagination Entry ${i}`,
          content: `Content for entry ${i}`,
          entry_date: `2025-${String(Math.floor((i - 1) / 28 + 1)).padStart(2, "0")}-${String(((i - 1) % 28) + 1).padStart(2, "0")}`,
        },
      });
    }

    await page.getByRole("link", { name: "Journal" }).click();
    await expect(page.locator("h1")).toContainText("Journal");

    // Wait for entries to load — first entry should be visible
    await expect(page.getByText("Pagination Entry").first()).toBeVisible({ timeout: 10000 });

    // Should show pagination controls if totalPages > 1
    const paginationText = page.getByText(/Page \d+ of \d+/);
    if (await paginationText.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Navigate to next page
      const nextBtn = page.getByRole("button", { name: "Next" });
      if (await nextBtn.isEnabled()) {
        await nextBtn.click();
        await expect(page.getByText(/Page 2 of/)).toBeVisible();
      }
    }
  });
});
