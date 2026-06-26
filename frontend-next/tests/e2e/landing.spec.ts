import { test, expect } from "@playwright/test";

test("landing renders headline and form", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /14-agent research desk/i })).toBeVisible();
  await expect(page.getByPlaceholder("AAPL", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /run research/i })).toBeVisible();
});

test("landing requires demo access code before starting live research", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /run research/i }).click();

  await expect(page).toHaveURL(/\/$/);
  await expect(page.locator("#demo-access-error")).toHaveText("Enter the demo access code to run live research.");
  await expect(page.getByPlaceholder("Demo access code")).toBeFocused();
});
