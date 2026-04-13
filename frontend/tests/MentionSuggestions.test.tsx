import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import MentionSuggestions from "../src/components/MentionSuggestions";

vi.mock("../src/api/mentions", () => ({
  getEntityNames: vi.fn().mockResolvedValue({
    goals: [
      { id: "g-1", name: "Squat 405" },
      { id: "g-2", name: "Run Marathon" },
    ],
    metric_types: [{ id: "m-1", name: "Body Weight" }],
    exercise_types: [
      { id: "e-1", name: "Back Squat" },
      { id: "e-2", name: "Bench Press" },
    ],
  }),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("MentionSuggestions", () => {
  it("suggests entity when name appears in text", async () => {
    const onInsert = vi.fn();
    render(
      <MemoryRouter>
        <MentionSuggestions content="Did some back squats today" onInsert={onInsert} />
      </MemoryRouter>,
    );

    // Should suggest Back Squat since "back squats" contains the words "back" and "squat"
    expect(await screen.findByText(/Back Squat/)).toBeInTheDocument();
  });

  it("does not suggest already-mentioned entities", async () => {
    const onInsert = vi.fn();
    render(
      <MemoryRouter>
        <MentionSuggestions
          content="Did some back squats today [[exercise:Back Squat]]"
          onInsert={onInsert}
        />
      </MemoryRouter>,
    );

    // Wait for entity names to load, then verify Back Squat is NOT suggested
    // (it's already mentioned). No other entity matches either, so no buttons.
    await vi.waitFor(() => {
      const buttons = screen.queryAllByRole("button");
      const texts = buttons.map((b) => b.textContent);
      expect(texts.join(",")).not.toContain("Back Squat");
    });
  });

  it("clicking suggestion calls onInsert with mention syntax", async () => {
    const onInsert = vi.fn();
    render(
      <MemoryRouter>
        <MentionSuggestions content="Did some back squats today" onInsert={onInsert} />
      </MemoryRouter>,
    );

    const button = await screen.findByRole("button", { name: /Back Squat/ });
    button.click();
    expect(onInsert).toHaveBeenCalledWith("[[exercise:Back Squat]]");
  });

  it("shows no suggestions when no matches", async () => {
    const onInsert = vi.fn();
    const { container } = render(
      <MemoryRouter>
        <MentionSuggestions content="Just a random note about nothing" onInsert={onInsert} />
      </MemoryRouter>,
    );

    // Wait a tick for async entity names load
    await vi.waitFor(() => {
      const buttons = container.querySelectorAll("button");
      expect(buttons.length).toBe(0);
    });
  });
});
