import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { getEntityNames } from "../api/mentions";
import type { EntityNames } from "../types/mention";

interface AutocompleteItem {
  type: string;
  shortType: string;
  name: string;
  icon: string;
}

const TYPE_MAP: { key: keyof EntityNames; shortType: string; label: string; icon: string }[] = [
  { key: "goals", shortType: "goal", label: "Goals", icon: "🎯" },
  { key: "metric_types", shortType: "metric", label: "Metrics", icon: "📊" },
  { key: "exercise_types", shortType: "exercise", label: "Exercises", icon: "🏋️" },
];

/**
 * Get the pixel position of a character offset inside MDEditor's visible
 * <pre><code> element using the Range API.  Returns coordinates relative
 * to `container`.
 */
function getCaretPixelPos(
  container: HTMLDivElement,
  charOffset: number,
): { top: number; left: number } | null {
  // MDEditor renders the visible (syntax-highlighted) text inside
  // .w-md-editor-text-pre > code.  Walk its text nodes to place a
  // collapsed Range at the right character offset.
  const codeEl = container.querySelector<HTMLElement>(
    ".w-md-editor-text-pre > code, .w-md-editor-text-pre",
  );
  if (!codeEl) return null;

  const walker = document.createTreeWalker(codeEl, NodeFilter.SHOW_TEXT);
  let remaining = charOffset;

  while (walker.nextNode()) {
    const textNode = walker.currentNode as Text;
    if (remaining <= textNode.length) {
      const range = document.createRange();
      range.setStart(textNode, remaining);
      range.collapse(true);
      const rect = range.getBoundingClientRect();
      const containerRect = container.getBoundingClientRect();
      return {
        top: rect.bottom - containerRect.top,
        left: rect.left - containerRect.left,
      };
    }
    remaining -= textNode.length;
  }

  return null;
}

interface MentionAutocompleteProps {
  containerRef: React.RefObject<HTMLDivElement | null>;
  value: string;
  onInsert: (before: string, mention: string, after: string) => void;
}

/**
 * Find the cursor position from the underlying textarea inside the MDEditor.
 * Returns -1 if not found.
 */
function getCursorPos(container: HTMLDivElement | null): number {
  if (!container) return -1;
  const textarea = container.querySelector("textarea");
  return textarea ? textarea.selectionStart : -1;
}

export default function MentionAutocomplete({
  containerRef,
  value,
  onInsert,
}: MentionAutocompleteProps) {
  const [entityNames, setEntityNames] = useState<EntityNames | null>(null);
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState("");
  const [triggerPos, setTriggerPos] = useState(-1);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const prevValueRef = useRef(value);

  // Fetch entity names on mount
  useEffect(() => {
    getEntityNames()
      .then(setEntityNames)
      .catch(() => {});
  }, []);

  // Detect [[ trigger from value changes
  useEffect(() => {
    const prev = prevValueRef.current;
    prevValueRef.current = value;

    // Only react to value growing (user typing, not deletions from autocomplete inserts)
    if (value.length <= prev.length && !open) return;

    const cursorPos = getCursorPos(containerRef.current);
    if (cursorPos < 0) return;

    if (open) {
      // If we have a valid trigger, update filter text between trigger+2 and cursor
      if (triggerPos >= 0 && cursorPos >= triggerPos + 2) {
        const filterText = value.slice(triggerPos + 2, cursorPos);
        // Close if user typed ]] or moved cursor before trigger
        if (filterText.includes("]]") || cursorPos < triggerPos) {
          setOpen(false);
          setFilter("");
          return;
        }
        setFilter(filterText);
        setSelectedIndex(0);
      } else {
        setOpen(false);
        setFilter("");
      }
    } else {
      // Check for [[ trigger: the two characters before cursor should be [[
      if (cursorPos >= 2 && value.slice(cursorPos - 2, cursorPos) === "[[") {
        setTriggerPos(cursorPos - 2);
        setFilter("");
        setOpen(true);
        setSelectedIndex(0);

        // Compute dropdown position from the visible code element
        const container = containerRef.current;
        if (container) {
          const pos = getCaretPixelPos(container, cursorPos);
          if (pos) setPosition(pos);
        }
      }
    }
  }, [value, open, triggerPos, containerRef]);

  // Build filtered items
  const items = useMemo(() => {
    const result: AutocompleteItem[] = [];
    if (entityNames) {
      const lowerFilter = filter.toLowerCase();
      for (const { key, shortType, icon } of TYPE_MAP) {
        for (const entity of entityNames[key]) {
          if (!lowerFilter || entity.name.toLowerCase().includes(lowerFilter)) {
            result.push({ type: key, shortType, name: entity.name, icon });
          }
        }
      }
    }
    return result;
  }, [entityNames, filter]);

  const handleSelect = useCallback(
    (item: AutocompleteItem) => {
      const mention = `[[${item.shortType}:${item.name}]]`;
      const before = value.slice(0, triggerPos);
      const cursorPos = getCursorPos(containerRef.current);
      const afterPos = cursorPos >= 0 ? cursorPos : value.length;
      const after = value.slice(afterPos);
      onInsert(before, mention, after);
      setOpen(false);
      setFilter("");
      setTriggerPos(-1);
    },
    [value, triggerPos, onInsert, containerRef],
  );

  // Capture keyboard events for navigation/selection
  useEffect(() => {
    if (!open) return;
    const container = containerRef.current;
    if (!container) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        setOpen(false);
        setFilter("");
        return;
      }

      if (e.key === "ArrowDown") {
        e.preventDefault();
        e.stopPropagation();
        setSelectedIndex((prev) => Math.min(prev + 1, items.length - 1));
        return;
      }

      if (e.key === "ArrowUp") {
        e.preventDefault();
        e.stopPropagation();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
        return;
      }

      if (e.key === "Enter" || e.key === "Tab") {
        const selected = items[selectedIndex];
        if (items.length > 0 && selected) {
          e.preventDefault();
          e.stopPropagation();
          handleSelect(selected);
        }
      }
    };

    // Use capture phase to intercept before MDEditor handles them
    container.addEventListener("keydown", handleKeyDown, true);
    return () => container.removeEventListener("keydown", handleKeyDown, true);
  }, [open, items, selectedIndex, handleSelect, containerRef]);

  // Close on click outside
  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
        setFilter("");
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  if (!open || items.length === 0) return null;

  return (
    <div
      ref={dropdownRef}
      className="absolute z-50 max-h-60 w-72 overflow-auto rounded-lg border border-gray-600 bg-dark-surface shadow-lg"
      style={position ? { top: position.top, left: position.left } : undefined}
      data-testid="mention-autocomplete"
    >
      {TYPE_MAP.map(({ key, shortType, label, icon }) => {
        const groupItems = items.filter((i) => i.type === key);
        if (groupItems.length === 0) return null;
        return (
          <div key={key}>
            <div className="px-3 py-1 text-xs font-semibold uppercase text-light-text/40">
              {icon} {label}
            </div>
            {groupItems.map((item) => {
              const globalIdx = items.indexOf(item);
              return (
                <button
                  key={`${shortType}-${item.name}`}
                  className={`w-full px-3 py-1.5 text-left text-sm text-light-text hover:bg-primary/20 ${
                    globalIdx === selectedIndex ? "bg-primary/20" : ""
                  }`}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    handleSelect(item);
                  }}
                >
                  {item.name}
                </button>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
