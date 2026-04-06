import { useEffect, useState } from "react";
import MDEditor, { commands } from "@uiw/react-md-editor";

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

  return (
    <div data-color-mode={colorMode}>
      <MDEditor
        value={value}
        onChange={(val) => onChange(val ?? "")}
        commands={toolbarCommands}
        extraCommands={[]}
        height={height}
        preview="edit"
        data-testid={testId}
      />
    </div>
  );
}
