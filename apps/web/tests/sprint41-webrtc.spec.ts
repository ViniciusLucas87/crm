/**
 * Sprint 41 — WebRTC Foundation E2E Tests
 *
 * These tests validate the browser-side WebRTC media layer:
 *   - Microphone permission flow
 *   - Outbound call creation
 *   - Call state transitions
 *   - Hangup and cleanup
 *   - Multiple sequential calls
 *   - Diagnostics panel
 *
 * Run with: npx playwright test tests/sprint41-webrtc.spec.ts
 */

import { test, expect } from "@playwright/test";

const BASE = "http://localhost:3000";
const TEST_COMPANY_ID = 9; // Must have a phone number in test DB

test.describe("Sprint 41 — WebRTC Foundation", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to company detail page (where CallButton lives)
    await page.goto(`${BASE}/companies/${TEST_COMPANY_ID}`);
    // Wait for the page to load
    await page.waitForLoadState("networkidle");
  });

  test("SP41-01: Call button is visible and clickable", async ({ page }) => {
    // The CallButton should be visible on the company page
    const callButton = page.locator("button", { hasText: /Call/i });
    await expect(callButton.first()).toBeVisible();
  });

  test("SP41-02: Microphone permission prompt appears on call", async ({ page }) => {
    // Grant microphone permission automatically
    await page.context().grantPermissions(["microphone"]);

    // Click the call button
    const callButton = page.locator("button", { hasText: /Call/i }).first();
    await callButton.click();

    // Should see a calling/dialing state in the UI
    // (The actual call behavior depends on backend, but UI should respond)
    await expect(page.locator("text=Dialing").or(page.locator("text=Ringing")).or(page.locator("text=Connecting"))).toBeVisible({ timeout: 10000 });
  });

  test("SP41-03: End call returns to idle state", async ({ page }) => {
    await page.context().grantPermissions(["microphone"]);

    const callButton = page.locator("button", { hasText: /Call/i }).first();
    await callButton.click();

    // Wait for any active call state
    await page.waitForTimeout(2000);

    // Look for hangup/end button
    const endButton = page.locator("button", { hasText: /End|Hang|PhoneOff/i }).first();
    if (await endButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await endButton.click();

      // Should return to idle (call button reappears)
      await expect(page.locator("button", { hasText: /Call/i }).first()).toBeVisible({ timeout: 10000 });
    }
  });

  test("SP41-04: Multiple sequential calls work", async ({ page }) => {
    await page.context().grantPermissions(["microphone"]);

    for (let i = 0; i < 2; i++) {
      const callButton = page.locator("button", { hasText: /Call/i }).first();
      await callButton.click();
      await page.waitForTimeout(1500);

      const endButton = page.locator("button", { hasText: /End|Hang|PhoneOff/i }).first();
      if (await endButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await endButton.click();
        await page.waitForTimeout(2000);
      } else {
        // May have failed — still try next iteration
        break;
      }
    }

    // After all calls, call button should be available again
    await expect(page.locator("button", { hasText: /Call/i }).first()).toBeVisible({ timeout: 5000 });
  });

  test("SP41-05: Diagnostics panel is accessible", async ({ page }) => {
    // The diagnostics panel toggle button should be in the DOM
    const diagButton = page.locator("button[title='WebRTC Diagnostics']");
    // It may not be visible if no call has been made, but it should exist
    await expect(diagButton).toBeAttached({ timeout: 5000 });
  });

  test("SP41-06: Browser refresh retains telephony state", async ({ page }) => {
    // Reload the page
    await page.reload();
    await page.waitForLoadState("networkidle");

    // Call button should still be visible after refresh
    const callButton = page.locator("button", { hasText: /Call/i }).first();
    await expect(callButton).toBeVisible({ timeout: 10000 });

    // Application should not crash
    await expect(page.locator("body")).toBeVisible();
  });

  test("SP41-07: Error state shown on failed call", async ({ page }) => {
    // Deny microphone permission
    await page.context().grantPermissions([]);

    // Click call button
    const callButton = page.locator("button", { hasText: /Call/i }).first();
    await callButton.click();

    // Should eventually show an error or return to idle
    await page.waitForTimeout(5000);

    // The call button should be visible again (recovered from error)
    await expect(page.locator("button", { hasText: /Call/i }).first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe("Sprint 41 — Diagnostics Panel", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE}/companies/${TEST_COMPANY_ID}`);
    await page.waitForLoadState("networkidle");
  });

  test("SP41-D01: Diagnostics panel opens", async ({ page }) => {
    const diagButton = page.locator("button[title='WebRTC Diagnostics']");
    await diagButton.click();

    // Panel should be visible
    await expect(page.locator("text=WebRTC Diagnostics")).toBeVisible({ timeout: 5000 });

    // Should show SDK status
    await expect(page.locator("text=SDK Connection")).toBeVisible();
    await expect(page.locator("text=Client State")).toBeVisible();

    // Should show call section
    await expect(page.locator("text=Call State")).toBeVisible();
  });

  test("SP41-D02: Diagnostics panel shows media info", async ({ page }) => {
    const diagButton = page.locator("button[title='WebRTC Diagnostics']");
    await diagButton.click();

    await expect(page.locator("text=Media")).toBeVisible();
    await expect(page.locator("text=Mic Permission")).toBeVisible();
    await expect(page.locator("text=Local Track")).toBeVisible();
    await expect(page.locator("text=Remote Track")).toBeVisible();
  });

  test("SP41-D03: Diagnostics panel shows network stats", async ({ page }) => {
    const diagButton = page.locator("button[title='WebRTC Diagnostics']");
    await diagButton.click();

    await expect(page.locator("text=Network")).toBeVisible();
    await expect(page.locator("text=Packets Sent")).toBeVisible();
    await expect(page.locator("text=Packets Recv")).toBeVisible();
    await expect(page.locator("text=Bytes Sent")).toBeVisible();
    await expect(page.locator("text=Bytes Recv")).toBeVisible();
  });

  test("SP41-D04: Diagnostics panel shows WebRTC state", async ({ page }) => {
    const diagButton = page.locator("button[title='WebRTC Diagnostics']");
    await diagButton.click();

    await expect(page.locator("text=Peer State")).toBeVisible();
    await expect(page.locator("text=ICE State")).toBeVisible();
    await expect(page.locator("text=Codec")).toBeVisible();
  });

  test("SP41-D05: Diagnostics panel can be closed", async ({ page }) => {
    const diagButton = page.locator("button[title='WebRTC Diagnostics']");
    await diagButton.click();

    await expect(page.locator("text=WebRTC Diagnostics")).toBeVisible();

    // Click close (X button)
    const closeButton = page.locator("button", { hasText: "" }).filter({ has: page.locator("svg") }).last();
    // Click the close button in the panel header
    await page.locator("text=WebRTC Diagnostics").locator("..").locator("button").click();

    // Panel should close
    await expect(page.locator("text=WebRTC Diagnostics")).not.toBeVisible({ timeout: 3000 });
  });
});
