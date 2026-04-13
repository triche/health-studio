import { useCallback, useEffect, useRef, useState } from "react";
import MDEditor, { commands } from "@uiw/react-md-editor";
import MentionAutocomplete from "./MentionAutocomplete";
import MentionSuggestions from "./MentionSuggestions";

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  height?: number;
  "data-testid"?: string;
}

const toolbarCommands = [
  commands.bold,
  commands.italic,
  commands.strikethrough,
  commands.divider,
  commands.group([commands.title1, commands.title2, commands.title3, commands.title4], {
    name: "title",
    groupName: "title",
    buttonProps: { "aria-label": "Insert heading" },
  }),
  commands.quote,
  commands.divider,
  commands.unorderedListCommand,
  commands.orderedListCommand,
  commands.checkedListCommand,
  commands.divider,
  commands.link,
  commands.image,
  commands.divider,
  commands.hr,
];

export default function MarkdownEditor({
  value,
  onChange,
  height = 200,
  "data-testid": testId,
}: MarkdownEditorProps) {
  const [colorMode, setColorMode] = useState<"light" | "dark">(() =>
    document.documentElement.classList.contains("dark") ? "dark" : "light",
  );
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new MutationObserver(() => {
      setColorMode(document.documentElement.classList.contains("dark") ? "dark" : "light");
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });
    return () => observer.disconnect();
  }, []);

  const handleInsert = useCallback(
    (before: string, mention: string, after: string) => {
      onChange(before + mention + after);
    },
    [onChange],
  );

  const handleSuggestionInsert = useCallback(
    (mention: string) => {
      // Insert at cursor position if available, otherwise append
      const textarea = containerRef.current?.querySelector("textarea");
      const cursorPos = textarea?.selectionStart ?? value.length;
      const before = value.slice(0, cursorPos);
      const after = value.slice(cursorPos);
      const spaceBefore = before.length > 0 && !before.endsWith(" ") ? " " : "";
      const spaceAfter = after.length > 0 && !after.startsWith(" ") ? " " : "";
      onChange(before + spaceBefore + mention + spaceAfter + after);
    },
    [onChange, value],
  );

  return (
    <div data-color-mode={colorMode} ref={containerRef} className="relative">
      <MDEditor
        value={value}
        onChange={(val) => onChange(val ?? "")}
        commands={toolbarCommands}
        extraCommands={[]}
        height={height}
        preview="edit"
        data-testid={testId}
      />
      <MentionAutocomplete containerRef={containerRef} value={value} onInsert={handleInsert} />
      <MentionSuggestions content={value} onInsert={handleSuggestionInsert} />
    </div>
  );
}
