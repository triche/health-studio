import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "../src/App";

describe("App", () => {
  it("renders the Health Studio heading", () => {
    render(<App />);
    expect(screen.getByText("Health Studio")).toBeInTheDocument();
  });
});
