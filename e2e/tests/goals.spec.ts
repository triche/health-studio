import { test, expect } from "../fixtures/auth";

test.describe("Goals", () => {
  test("create a goal linked to a metric, verify progress, complete it", async ({
    authenticatedPage: page,
  }) => {
    // Navigate to Goals
    await page.getByRole("link", { name: "Goals" }).click();
    await expect(page.locator("h1")).toContainText("Goals");

    // Create a new goal
    await page.getByRole("button", { name: "New Goal" }).click();

    await page.locator("#goal-title").fill("Reach 175 lbs");
    await page.locator("#goal-description").fill("Target weight loss goal for Q3");

    // Select target type: Metric
    await page.locator("#target-type").selectOption("metric");

    // Select metric: Weight (label includes unit)
    const targetIdSelect = page.locator("#target-id");
    await targetIdSelect.waitFor({ state: "visible" });
    // Wait for options to populate from API
    await page.locator("#target-id option:not([value=''])").first().waitFor({ state: "attached", timeout: 10000 });
    await targetIdSelect.selectOption({ label: "Weight (lbs)" });

    // Set target value
    await page.locator("#target-value").fill("175");

    // Set start value
    const startValue = page.locator("#start-value");
    if (await startValue.isVisible()) {
      await startValue.fill("185");
    }

    // Check "Lower is better" since we're losing weight
    const lowerIsBetter = page.getByLabel("Lower is better");
    if (await lowerIsBetter.isVisible()) {
      await lowerIsBetter.check();
    }

    // Set deadline
    await page.locator("#deadline").fill("2025-12-31");

    // Save goal
    await page.getByRole("button", { name: "Save Goal" }).click();

    // Verify goal appears in the list
    await expect(page.getByText("Reach 175 lbs")).toBeVisible();
    // Status badge <span> shows "active" (avoid matching the filter <option>Active</option>)
    await expect(page.locator("span").filter({ hasText: /^active$/ })).toBeVisible();

    // Mark goal as completed
    await page.getByRole("button", { name: "Complete" }).first().click();
    await expect(page.locator("span").filter({ hasText: /^completed$/ })).toBeVisible();
  });

  test("create a goal linked to an exercise result", async ({ authenticatedPage: page }) => {
    await page.getByRole("link", { name: "Goals" }).click();
    await expect(page.locator("h1")).toContainText("Goals");

    // Create a goal for Back Squat PR
    await page.getByRole("button", { name: "New Goal" }).click();

    await page.locator("#goal-title").fill("Squat 400 lbs");
    await page.locator("#goal-description").fill("Hit a 400lb back squat");

    // Select target type: Exercise Result (value is "result" not "exercise")
    await page.locator("#target-type").selectOption("result");

    const targetIdSelect = page.locator("#target-id");
    await targetIdSelect.waitFor({ state: "visible" });
    await page.locator("#target-id option:not([value=''])").first().waitFor({ state: "attached", timeout: 10000 });
    await targetIdSelect.selectOption({ label: "Back Squat (lbs)" });

    await page.locator("#target-value").fill("400");

    const startValue = page.locator("#start-value");
    if (await startValue.isVisible()) {
      await startValue.fill("315");
    }

    await page.locator("#deadline").fill("2025-12-31");

    await page.getByRole("button", { name: "Save Goal" }).click();
    await expect(page.getByText("Squat 400 lbs")).toBeVisible();
  });

  test("filter goals by status", async ({ authenticatedPage: page }) => {
    await page.getByRole("link", { name: "Goals" }).click();
    await expect(page.locator("h1")).toContainText("Goals");

    // Create a goal first
    await page.getByRole("button", { name: "New Goal" }).click();
    await page.locator("#goal-title").fill("Filterable Goal");
    await page.locator("#goal-description").fill("For filter testing");
    await page.locator("#deadline").fill("2025-12-31");
    // Must select a target for the form to submit
    await page.locator("#target-type").selectOption("metric");
    const targetIdSelect = page.locator("#target-id");
    await targetIdSelect.waitFor({ state: "visible" });
    await page.locator("#target-id option:not([value=''])").first().waitFor({ state: "attached", timeout: 10000 });
    await targetIdSelect.selectOption({ label: "Weight (lbs)" });
    await page.locator("#target-value").fill("100");
    await page.getByRole("button", { name: "Save Goal" }).click();
    await expect(page.getByText("Filterable Goal")).toBeVisible();

    // Filter by active
    await page.locator("#status-filter").selectOption("active");
    await expect(page.getByText("Filterable Goal")).toBeVisible();

    // Filter by completed — the new goal shouldn't appear
    await page.locator("#status-filter").selectOption("completed");
    await expect(page.getByText("Filterable Goal")).not.toBeVisible();

    // Back to all
    await page.locator("#status-filter").selectOption("");
  });

  test("edit and delete a goal", async ({ authenticatedPage: page }) => {
    await page.getByRole("link", { name: "Goals" }).click();

    // Create a goal
    await page.getByRole("button", { name: "New Goal" }).click();
    await page.locator("#goal-title").fill("Deletable Goal");
    await page.locator("#goal-description").fill("Will be deleted");
    await page.locator("#deadline").fill("2025-12-31");
    await page.locator("#target-type").selectOption("metric");
    const targetIdSelect = page.locator("#target-id");
    await targetIdSelect.waitFor({ state: "visible" });
    await page.locator("#target-id option:not([value=''])").first().waitFor({ state: "attached", timeout: 10000 });
    await targetIdSelect.selectOption({ label: "Weight (lbs)" });
    await page.locator("#target-value").fill("100");
    await page.getByRole("button", { name: "Save Goal" }).click();
    await expect(page.getByText("Deletable Goal")).toBeVisible();

    // Edit the goal
    await page.getByRole("button", { name: "Edit" }).first().click();
    await page.locator("#goal-title").clear();
    await page.locator("#goal-title").fill("Renamed Goal");
    await page.getByRole("button", { name: "Save Goal" }).click();
    await expect(page.getByText("Renamed Goal")).toBeVisible();

    // Delete the goal
    await page.getByRole("button", { name: "Delete" }).first().click();
    await expect(page.getByText("Renamed Goal")).not.toBeVisible();
  });
});
