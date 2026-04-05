import { test as setup, expect } from "@playwright/test";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

setup("verify app is running", async ({ request }) => {
  // Check backend health
  const healthResp = await request.get(`${API_URL}/api/health`);
  expect(healthResp.ok()).toBeTruthy();

  // Check frontend is serving
  const frontendResp = await request.get("/");
  expect(frontendResp.ok()).toBeTruthy();
});
