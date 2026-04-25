import { test, expect } from "@playwright/test";

test("landing renders headline and form", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /14-agent research desk/i })).toBeVisible();
  await expect(page.getByPlaceholder("AAPL", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /run research/i })).toBeVisible();
});
