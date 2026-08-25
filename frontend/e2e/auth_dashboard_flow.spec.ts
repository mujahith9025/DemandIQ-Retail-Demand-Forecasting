import { test, expect } from "@playwright/test";

test.describe("DemandIQ E2E Production Flow", () => {
  test("User can log in, view executive dashboard KPIs, and navigate to forecasts", async ({
    page,
  }) => {
    // 1. Visit Login Page
    await page.goto("http://localhost:3000/login");
    await expect(page).toHaveTitle(/DemandIQ/i);

    // 2. Click 1-Click Supply Planner Demo Preset
    const plannerButton = page.locator("button:has-text('Supply Planner')");
    if (await plannerButton.isVisible()) {
      await plannerButton.click();
    } else {
      await page.fill('input[type="email"]', "planner@demandiq.io");
      await page.fill('input[type="password"]', "plannerpassword123");
    }

    // 3. Submit Login Form
    await page.click('button[type="submit"]');

    // 4. Verify Redirection to Executive Dashboard
    await page.waitForURL("**/dashboard", { timeout: 10000 });
    await expect(page.locator("h1")).toContainText("Executive Dashboard");

    // 5. Verify KPI Cards Visible
    await expect(page.locator("text=Projected 30D Revenue")).toBeVisible();
    await expect(page.locator("text=Forecast Accuracy")).toBeVisible();

    // 6. Navigate to Demand Forecasts Engine
    await page.click('a[href="/forecasts"]');
    await page.waitForURL("**/forecasts");
    await expect(page.locator("h1")).toContainText("Demand Forecasting Engine");

    // 7. Verify Forecast Model Selector & Confidence Band
    await expect(page.locator("select").first()).toBeVisible();
    await expect(page.locator("text=Weekly Demand Trajectory")).toBeVisible();
  });
});
