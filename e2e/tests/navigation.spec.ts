import { test, expect } from "../fixtures/auth";

test.describe("Navigation", () => {
  test("sidebar links navigate to all pages", async ({ authenticatedPage: page }) => {
    const pages = [
      { link: "Dashboard", heading: "Dashboard" },
      { link: "Journal", heading: "Journal" },
      { link: "Metrics", heading: "Metrics" },
      { link: "Results", heading: "Results" },
      { link: "Goals", heading: "Goals" },
    ];

    for (const { link, heading } of pages) {
      await page.getByRole("link", { name: link }).click();
      await expect(page.locator("h1").first()).toContainText(heading);
    }

    // Settings via button
    await page.getByRole("button", { name: "Settings" }).click();
    await expect(page.locator("h1")).toContainText("Settings");
  });

  test("browser back/forward navigation works", async ({ authenticatedPage: page }) => {
    // Navigate through pages
    await page.getByRole("link", { name: "Journal" }).click();
    await expect(page.locator("h1")).toContainText("Journal");

    await page.getByRole("link", { name: "Metrics" }).click();
    await expect(page.locator("h1")).toContainText("Metrics");

    await page.getByRole("link", { name: "Results" }).click();
    await expect(page.locator("h1")).toContainText("Results");

    // Go back
    await page.goBack();
    await expect(page.locator("h1")).toContainText("Metrics");

    await page.goBack();
    await expect(page.locator("h1")).toContainText("Journal");

    // Go forward
    await page.goForward();
    await expect(page.locator("h1")).toContainText("Metrics");
  });

  test("deep link loads the correct page", async ({ authenticatedPage: page }) => {
    await page.goto("/journals");
    await expect(page.locator("h1")).toContainText("Journal");

    await page.goto("/metrics");
    await expect(page.locator("h1")).toContainText("Metrics");

    await page.goto("/results");
    await expect(page.locator("h1")).toContainText("Results");

    await page.goto("/goals");
    await expect(page.locator("h1")).toContainText("Goals");

    await page.goto("/settings");
    await expect(page.locator("h1")).toContainText("Settings");
  });
});
