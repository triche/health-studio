import { useState, useEffect, useRef } from "react";
import { listTags } from "../api/tags";
import type { TagCount } from "../types/tag";

interface TagInputProps {
  tags: string[];
  onChange: (tags: string[]) => void;
}

export default function TagInput({ tags, onChange }: TagInputProps) {
  const [input, setInput] = useState("");
  const [suggestions, setSuggestions] = useState<TagCount[]>([]);
  const [allTags, setAllTags] = useState<TagCount[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listTags()
      .then(setAllTags)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (input.length > 0) {
      const filtered = allTags.filter(
        (t) => t.tag.includes(input.toLowerCase()) && !tags.includes(t.tag),
      );
      setSuggestions(filtered);
      setShowSuggestions(filtered.length > 0);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, [input, allTags, tags]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const addTag = (value: string) => {
    const tag = value.trim().toLowerCase();
    if (tag && !tags.includes(tag)) {
      onChange([...tags, tag]);
    }
    setInput("");
    setShowSuggestions(false);
  };

  const removeTag = (index: number) => {
    onChange(tags.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (input.trim()) addTag(input);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value.endsWith(",")) {
      const tag = value.slice(0, -1);
      if (tag.trim()) addTag(tag);
    } else {
      setInput(value);
    }
  };

  return (
    <div ref={wrapperRef} className="relative">
      <div className="flex flex-wrap items-center gap-1.5 rounded-lg border border-gray-600 bg-dark-surface px-2 py-1.5">
        {tags.map((tag, i) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 rounded-full bg-primary/20 px-2 py-0.5 text-xs font-medium text-primary"
          >
            {tag}
            <button
              type="button"
              aria-label={`Remove ${tag}`}
              onClick={() => removeTag(i)}
              className="ml-0.5 text-primary/60 hover:text-primary"
            >
              ×
            </button>
          </span>
        ))}
        <input
          type="text"
          value={input}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Add tag..."
          className="min-w-[80px] flex-1 bg-transparent text-sm text-light-text outline-none placeholder:text-light-text/40"
        />
      </div>
      {showSuggestions && (
        <ul className="absolute z-10 mt-1 max-h-40 w-full overflow-auto rounded-lg border border-gray-600 bg-dark-surface shadow-lg">
          {suggestions.map((s) => (
            <li key={s.tag}>
              <button
                type="button"
                onClick={() => addTag(s.tag)}
                className="flex w-full items-center justify-between px-3 py-1.5 text-sm text-light-text hover:bg-slate-700"
              >
                <span>{s.tag}</span>
                <span className="text-xs text-light-text/40">{s.count}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
