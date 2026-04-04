import { render, screen, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ToastProvider } from "../src/components/Toast";
import { useToast } from "../src/components/ToastContext";

beforeEach(() => {
  vi.useFakeTimers();
});

function TestConsumer() {
  const { showToast } = useToast();
  return (
    <div>
      <button onClick={() => showToast("Item saved", "success")}>Success</button>
      <button onClick={() => showToast("Something went wrong", "error")}>Error</button>
      <button onClick={() => showToast("Heads up", "info")}>Info</button>
    </div>
  );
}

describe("Toast", () => {
  it("shows a success toast when triggered", async () => {
    render(
      <ToastProvider>
        <TestConsumer />
      </ToastProvider>,
    );

    act(() => {
      screen.getByText("Success").click();
    });

    expect(screen.getByText("Item saved")).toBeInTheDocument();
  });

  it("shows an error toast when triggered", async () => {
    render(
      <ToastProvider>
        <TestConsumer />
      </ToastProvider>,
    );

    act(() => {
      screen.getByText("Error").click();
    });

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("shows an info toast when triggered", async () => {
    render(
      <ToastProvider>
        <TestConsumer />
      </ToastProvider>,
    );

    act(() => {
      screen.getByText("Info").click();
    });

    expect(screen.getByText("Heads up")).toBeInTheDocument();
  });

  it("auto-dismisses toast after timeout", async () => {
    render(
      <ToastProvider>
        <TestConsumer />
      </ToastProvider>,
    );

    act(() => {
      screen.getByText("Success").click();
    });

    expect(screen.getByText("Item saved")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(4000);
    });

    expect(screen.queryByText("Item saved")).not.toBeInTheDocument();
  });

  it("can show multiple toasts", async () => {
    render(
      <ToastProvider>
        <TestConsumer />
      </ToastProvider>,
    );

    act(() => {
      screen.getByText("Success").click();
    });
    act(() => {
      screen.getByText("Error").click();
    });

    expect(screen.getByText("Item saved")).toBeInTheDocument();
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });
});
