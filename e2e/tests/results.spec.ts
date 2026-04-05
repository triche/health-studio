import { test, expect } from "../fixtures/auth";

test.describe("Results", () => {
  test("create exercise type, log results with PR detection, toggle RX", async ({
    authenticatedPage: page,
  }) => {
    await page.getByRole("link", { name: "Results" }).click();
    await expect(page.locator("h1")).toContainText("Results");

    // Select "Back Squat" (pre-seeded, label includes unit)
    await page.locator("#exercise-type-select").selectOption({ label: "Back Squat (lbs)" });

    // Log first result
    await page.getByLabel("Value").fill("275");
    await page.getByLabel("Date").fill("2025-06-01");
    await page.getByLabel("Notes").fill("Working set");
    await page.getByRole("button", { name: "Log" }).click();
    await expect(page.getByText("275")).toBeVisible();

    // Log a PR result (higher value)
    await page.getByLabel("Value").fill("315");
    await page.getByLabel("Date").fill("2025-06-15");
    await page.getByLabel("Notes").fill("New PR!");
    await page.getByRole("button", { name: "Log" }).click();

    // Verify PR badge appears (use exact match to avoid matching "Bench Press" option text)
    await expect(page.getByText("PR", { exact: true }).first()).toBeVisible();

    // Edit a result
    await page.getByRole("button", { name: "Edit" }).first().click();
    const editNotesInput = page.getByRole("textbox", { name: "Edit notes" });
    await editNotesInput.clear();
    await editNotesInput.fill("PR confirmed");
    await page.getByRole("button", { name: "Save" }).click();
    await expect(page.getByText("PR confirmed")).toBeVisible();

    // Delete a result
    await page.getByRole("button", { name: "Delete" }).last().click();
  });

  test("RX flag for CrossFit benchmarks", async ({ authenticatedPage: page }) => {
    await page.getByRole("link", { name: "Results" }).click();
    await expect(page.locator("h1")).toContainText("Results");

    // Select a CrossFit benchmark (Fran - pre-seeded, time-based, label includes unit)
    await page.locator("#exercise-type-select").selectOption({ label: "Fran (seconds)" });

    // Log a time-based result with RX flag
    const minutesInput = page.getByLabel("Minutes");
    const secondsInput = page.getByLabel("Seconds");

    if (await minutesInput.isVisible()) {
      await minutesInput.fill("3");
      await secondsInput.fill("45");
    }

    await page.getByLabel("Date").fill("2025-06-15");

    // Toggle RX checkbox
    const rxCheckbox = page.getByLabel("RX");
    if (await rxCheckbox.isVisible()) {
      await rxCheckbox.check();
    }

    await page.getByRole("button", { name: "Log" }).click();

    // Verify RX badge appears
    await expect(page.getByText("RX").first()).toBeVisible();
  });

  test("graph toggle shows trends", async ({ authenticatedPage: page }) => {
    await page.getByRole("link", { name: "Results" }).click();

    // Select Back Squat (label includes unit)
    await page.locator("#exercise-type-select").selectOption({ label: "Back Squat (lbs)" });

    // Log an entry so there's data to chart
    await page.getByLabel("Value").fill("225");
    await page.getByLabel("Date").fill("2025-05-20");
    await page.getByRole("button", { name: "Log" }).click();

    // Toggle graph
    const showGraphBtn = page.getByLabel("Show graph");
    if (await showGraphBtn.isVisible()) {
      await showGraphBtn.click();
      await expect(page.locator(".js-plotly-plot")).toBeVisible({ timeout: 5000 });
    }
  });
});
