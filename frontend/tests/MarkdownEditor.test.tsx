import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock @uiw/react-md-editor to avoid complex rendering in tests
vi.mock("@uiw/react-md-editor", () => {
  const commands: Record<string, unknown> = {
    bold: { name: "bold" },
    italic: { name: "italic" },
    strikethrough: { name: "strikethrough" },
    title1: { name: "title1" },
    title2: { name: "title2" },
    title3: { name: "title3" },
    title4: { name: "title4" },
    quote: { name: "quote" },
    unorderedListCommand: { name: "unordered-list" },
    orderedListCommand: { name: "ordered-list" },
    checkedListCommand: { name: "checked-list" },
    link: { name: "link" },
    image: { name: "image" },
    hr: { name: "hr" },
    divider: { name: "divider" },
    group: () => ({ name: "group" }),
  };
  const MDEditor = ({
    value,
    onChange,
    "data-testid": testId,
  }: {
    value: string;
    onChange: (v: string) => void;
    "data-testid"?: string;
    commands?: unknown[];
    "data-color-mode"?: string;
    height?: number;
  }) => (
    <textarea
      data-testid={testId || "md-editor"}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  );
  return { default: MDEditor, commands };
});

import MarkdownEditor from "../src/components/MarkdownEditor";

describe("MarkdownEditor", () => {
  const onChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders with initial value", () => {
    render(<MarkdownEditor value="Hello **world**" onChange={onChange} />);
    const editor = screen.getByTestId("md-editor");
    expect(editor).toBeInTheDocument();
    expect(editor).toHaveValue("Hello **world**");
  });

  it("calls onChange when text is entered", async () => {
    const user = userEvent.setup();
    render(<MarkdownEditor value="" onChange={onChange} />);
    const editor = screen.getByTestId("md-editor");
    await user.type(editor, "new text");
    expect(onChange).toHaveBeenCalled();
  });

  it("passes custom data-testid", () => {
    render(<MarkdownEditor value="" onChange={onChange} data-testid="custom-editor" />);
    expect(screen.getByTestId("custom-editor")).toBeInTheDocument();
  });
});
