import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

// Mock the API module
vi.mock("@/lib/api", () => ({
  fetchTodayWorkspace: vi.fn(),
  executeFollowUp: vi.fn(),
  acknowledgeReply: vi.fn(),
}));

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string }) =>
    React.createElement("a", { href, ...props }, children),
}));

// Mock the Shell
vi.mock("@/components/dashboard/shell", () => ({
  Shell: ({ children }: { children: React.ReactNode }) =>
    React.createElement("div", { "data-testid": "shell" }, children),
}));

import TodayScreen from "@/components/dashboard/today-screen";
import { fetchTodayWorkspace, executeFollowUp, acknowledgeReply } from "@/lib/api";

const mockFetchToday = fetchTodayWorkspace as ReturnType<typeof vi.fn>;
const mockExecuteFollowUp = executeFollowUp as ReturnType<typeof vi.fn>;
const mockAcknowledgeReply = acknowledgeReply as ReturnType<typeof vi.fn>;

const emptyWorkspace = {
  assessmentLeads: [],
  missedCalls: [],
  inboundReplies: [],
  overdueFollowUps: [],
  dueToday: [],
  upcoming: [],
  leadsNoNextAction: [],
  generatedAt: new Date().toISOString(),
};

describe("TodayScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state initially", () => {
    mockFetchToday.mockReturnValue(new Promise(() => {})); // never resolves
    render(<TodayScreen />);
    expect(screen.getByText(/loading/i)).toBeTruthy();
  });

  it("shows empty state when no items", async () => {
    mockFetchToday.mockResolvedValue(emptyWorkspace);
    render(<TodayScreen />);
    await waitFor(() => {
      expect(screen.getByText(/all caught up/i)).toBeTruthy();
    });
  });

  it("shows error state on fetch failure", async () => {
    mockFetchToday.mockRejectedValue(new Error("Network error"));
    render(<TodayScreen />);
    await waitFor(() => {
      expect(screen.getByText(/try again/i)).toBeTruthy();
    });
  });

  it("shows overdue task with actions", async () => {
    mockFetchToday.mockResolvedValue({
      ...emptyWorkspace,
      overdueFollowUps: [
        {
          id: 1, leadId: null, title: "Call Acme Corp",
          description: null, priority: "high", status: "open",
          dueDate: "2026-08-01", isCompleted: false, source: "follow_up",
          companyId: 10, companyName: "Acme Corp", contactId: null,
          contactName: null, contactEmail: null, contactPhone: null,
          ownerUserId: null, reason: "Overdue",
        },
      ],
    });
    render(<TodayScreen />);
    await waitFor(() => {
      expect(screen.getByText("Call Acme Corp")).toBeTruthy();
      expect(screen.getByText("Complete")).toBeTruthy();
      expect(screen.getByText("Reschedule")).toBeTruthy();
    });
  });

  it("calls executeFollowUp on complete with terminal outcome", async () => {
    mockFetchToday.mockResolvedValue({
      ...emptyWorkspace,
      dueToday: [
        {
          id: 2, leadId: null, title: "Send proposal",
          description: null, priority: "medium", status: "open",
          dueDate: new Date().toISOString().slice(0, 10), isCompleted: false,
          source: null, companyId: 20, companyName: "Beta Inc",
          contactId: null, contactName: null, contactEmail: null,
          contactPhone: null, ownerUserId: null, reason: "Due today",
        },
      ],
    });
    mockExecuteFollowUp.mockResolvedValue({
      taskId: 2, action: "completed", activityId: 5,
      nextTaskId: 3, message: "Task completed",
    });

    const user = userEvent.setup();
    render(<TodayScreen />);

    await waitFor(() => {
      expect(screen.getByText("Send proposal")).toBeTruthy();
    });

    // Select terminal outcome
    const select = screen.getByRole("combobox");
    await user.selectOptions(select, "won");

    await user.click(screen.getByText("Complete"));
    await waitFor(() => {
      expect(mockExecuteFollowUp).toHaveBeenCalledWith(2, expect.objectContaining({
        action: "complete",
        terminalOutcome: "won",
        idempotencyKey: expect.any(String),
      }));
      const call = mockExecuteFollowUp.mock.calls[0][1];
      expect(call.idempotencyKey).toBeTruthy();
      expect(call.idempotencyKey.length).toBeGreaterThan(10);
    });
  });

  it("shows guidance when Complete clicked without outcome or next step", async () => {
    mockFetchToday.mockResolvedValue({
      ...emptyWorkspace,
      dueToday: [
        {
          id: 3, leadId: null, title: "Empty complete test",
          description: null, priority: "low", status: "open",
          dueDate: new Date().toISOString().slice(0, 10), isCompleted: false,
          source: null, companyId: 30, companyName: "Test Inc",
          contactId: null, contactName: null, contactEmail: null,
          contactPhone: null, ownerUserId: null, reason: "Due today",
        },
      ],
    });

    const user = userEvent.setup();
    render(<TodayScreen />);

    await waitFor(() => {
      expect(screen.getByText("Empty complete test")).toBeTruthy();
    });

    await user.click(screen.getByText("Complete"));
    await waitFor(() => {
      expect(screen.getByText(/Choose a terminal outcome/i)).toBeTruthy();
    });
    expect(mockExecuteFollowUp).not.toHaveBeenCalled();
  });

  it("shows inbound reply with Acknowledge button", async () => {
    mockFetchToday.mockResolvedValue({
      ...emptyWorkspace,
      inboundReplies: [{
        id: 10, emailUuid: "u1", fromAddress: "lead@acme.com",
        subject: "Interested", receivedAt: new Date().toISOString(),
        companyId: 30, companyName: "Acme Corp", contactId: null,
        contactName: null, reason: "New inbound reply",
      }],
    });
    render(<TodayScreen />);
    await waitFor(() => {
      expect(screen.getByText("Acknowledge")).toBeTruthy();
    });
  });

  it("calls acknowledgeReply and refreshes on Acknowledge click", async () => {
    mockFetchToday.mockResolvedValue({
      ...emptyWorkspace,
      inboundReplies: [{
        id: 11, emailUuid: "u2", fromAddress: "test@example.com",
        subject: "Hello", receivedAt: new Date().toISOString(),
        companyId: 40, companyName: "TestCo", contactId: null,
        contactName: null, reason: "New inbound reply",
      }],
    });
    mockAcknowledgeReply.mockResolvedValue({ id: 11, status: "responded" });

    const user = userEvent.setup();
    render(<TodayScreen />);

    await waitFor(() => {
      expect(screen.getByText("Acknowledge")).toBeTruthy();
    });
    await user.click(screen.getByText("Acknowledge"));
    await waitFor(() => {
      expect(mockAcknowledgeReply).toHaveBeenCalledWith(11);
    });
  });

  it("shows error on failed acknowledge", async () => {
    mockFetchToday.mockResolvedValue({
      ...emptyWorkspace,
      inboundReplies: [{
        id: 12, emailUuid: "u3", fromAddress: "fail@test.com",
        subject: "Err", receivedAt: new Date().toISOString(),
        companyId: null, companyName: null, contactId: null,
        contactName: null, reason: "New inbound reply",
      }],
    });
    mockAcknowledgeReply.mockRejectedValue(new Error("Network error"));

    const user = userEvent.setup();
    render(<TodayScreen />);

    await waitFor(() => {
      expect(screen.getByText("Acknowledge")).toBeTruthy();
    });
    await user.click(screen.getByText("Acknowledge"));
    await waitFor(() => {
      expect(screen.getByText(/could not acknowledge/i)).toBeTruthy();
    });
  });
});
