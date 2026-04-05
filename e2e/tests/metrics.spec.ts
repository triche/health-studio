import { test, expect } from "../fixtures/auth";

test.describe("Metrics", () => {
  test("create a metric type, log entry, verify chart, edit, delete", async ({
    authenticatedPage: page,
  }) => {
    await page.getByRole("link", { name: "Metrics" }).click();
    await expect(page.locator("h1")).toContainText("Metrics");

    // Open manage panel and create a new metric type
    await page.getByRole("button", { name: "Manage types" }).click();
    await page.getByPlaceholder("Name").fill("Blood Pressure");
    await page.getByPlaceholder("Unit").fill("mmHg");
    await page.getByRole("button", { name: "Create" }).click();

    // Close the manage panel to avoid button name conflicts
    await page.getByRole("button", { name: "Manage types" }).click();

    // Select the new metric type (label includes unit)
    await page.locator("#metric-type-select").selectOption({ label: "Blood Pressure (mmHg)" });

    // Log a metric entry
    await page.getByLabel("Value").fill("120");
    await page.getByLabel("Date").fill("2025-06-15");
    await page.getByLabel("Notes").fill("Morning reading");
    await page.getByRole("button", { name: "Log" }).click();

    // Verify entry appears in the table
    await expect(page.getByText("Morning reading")).toBeVisible();
    await expect(page.getByText("120")).toBeVisible();

    // Show graph and verify it renders
    const showGraphBtn = page.getByLabel("Show graph");
    if (await showGraphBtn.isVisible()) {
      await showGraphBtn.click();
    }
    // Plotly chart should render (look for the plotly container)
    await expect(page.locator(".js-plotly-plot")).toBeVisible({ timeout: 5000 });

    // Edit the entry
    await page.getByRole("button", { name: "Edit" }).first().click();
    const editInput = page.getByRole("spinbutton", { name: "Edit value" });
    await editInput.clear();
    await editInput.fill("118");
    await page.getByRole("button", { name: "Save" }).click();
    await expect(page.getByRole("cell", { name: "118" })).toBeVisible();

    // Delete the entry
    await page.getByRole("button", { name: "Delete" }).first().click();
    await expect(page.getByText("Morning reading")).not.toBeVisible();
  });

  test("log entries for a seeded metric type", async ({ authenticatedPage: page }) => {
    await page.getByRole("link", { name: "Metrics" }).click();
    await expect(page.locator("h1")).toContainText("Metrics");

    // Select a pre-seeded metric type (Weight includes unit in label)
    await page.locator("#metric-type-select").selectOption({ label: "Weight (lbs)" });

    // Log an entry
    await page.getByLabel("Value").fill("175.5");
    await page.getByLabel("Date").fill("2025-06-10");
    await page.getByRole("button", { name: "Log" }).click();

    await expect(page.getByText("175.5")).toBeVisible();
  });
});
