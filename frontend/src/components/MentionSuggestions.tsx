import { useEffect, useMemo, useState } from "react";
import { getEntityNames } from "../api/mentions";
import type { EntityNames } from "../types/mention";

/** Stop words to ignore when matching entity names against content. */
const STOP_WORDS = new Set([
  "a",
  "an",
  "the",
  "and",
  "or",
  "but",
  "in",
  "on",
  "at",
  "to",
  "for",
  "of",
  "with",
  "is",
  "was",
  "are",
  "were",
  "be",
  "been",
  "am",
  "do",
  "did",
  "does",
  "has",
  "had",
  "have",
  "will",
  "would",
  "could",
  "should",
  "may",
  "might",
  "can",
  "shall",
  "i",
  "my",
  "me",
  "we",
  "our",
  "you",
  "your",
  "he",
  "she",
  "it",
  "they",
  "them",
  "their",
  "this",
  "that",
  "some",
  "just",
  "about",
  "so",
  "not",
  "no",
  "up",
  "out",
  "if",
  "then",
  "than",
  "too",
  "very",
  "also",
]);

const MENTION_REGEX = /\[\[([\w]+):([^\]]+)\]\]/g;

interface SuggestionItem {
  type: string;
  shortType: string;
  name: string;
  icon: string;
}

const TYPE_MAP: { key: keyof EntityNames; shortType: string; icon: string }[] = [
  { key: "goals", shortType: "goal", icon: "🎯" },
  { key: "metric_types", shortType: "metric", icon: "📊" },
  { key: "exercise_types", shortType: "exercise", icon: "🏋️" },
];

/**
 * Normalize a word for fuzzy matching: lowercase, strip trailing 's' for basic
 * plural handling.
 */
function normalize(word: string): string {
  const lower = word.toLowerCase();
  return lower.endsWith("s") && lower.length > 2 ? lower.slice(0, -1) : lower;
}

/**
 * Check if all significant words of an entity name appear in the content text.
 * Uses basic stemming (strip trailing 's') to match "squats" → "squat".
 */
function nameMatchesContent(entityName: string, contentWords: Set<string>): boolean {
  const nameWords = entityName
    .toLowerCase()
    .split(/\s+/)
    .filter((w) => w.length > 1 && !STOP_WORDS.has(w));
  if (nameWords.length === 0) return false;
  return nameWords.every((nw) => contentWords.has(normalize(nw)));
}

/** Extract the set of already-mentioned entity names from [[type:Name]] syntax. */
function getAlreadyMentioned(content: string): Set<string> {
  const mentioned = new Set<string>();
  let match: RegExpExecArray | null;
  MENTION_REGEX.lastIndex = 0;
  while ((match = MENTION_REGEX.exec(content)) !== null) {
    if (match[2]) mentioned.add(match[2].toLowerCase());
  }
  return mentioned;
}

interface MentionSuggestionsProps {
  content: string;
  onInsert: (mention: string) => void;
}

export default function MentionSuggestions({ content, onInsert }: MentionSuggestionsProps) {
  const [entityNames, setEntityNames] = useState<EntityNames | null>(null);

  useEffect(() => {
    getEntityNames()
      .then(setEntityNames)
      .catch(() => {});
  }, []);

  const suggestions = useMemo<SuggestionItem[]>(() => {
    if (!entityNames || !content.trim()) return [];

    // Tokenize content into normalized words
    const rawWords = content.toLowerCase().split(/[\s.,;:!?()[\]{}'"]+/);
    const contentWords = new Set(rawWords.filter((w) => w.length > 1).map(normalize));

    const alreadyMentioned = getAlreadyMentioned(content);

    const result: SuggestionItem[] = [];
    for (const { key, shortType, icon } of TYPE_MAP) {
      for (const entity of entityNames[key]) {
        // Skip if already mentioned
        if (alreadyMentioned.has(entity.name.toLowerCase())) continue;
        // Check if entity name words appear in content
        if (nameMatchesContent(entity.name, contentWords)) {
          result.push({ type: key, shortType, name: entity.name, icon });
        }
      }
    }
    return result;
  }, [entityNames, content]);

  if (suggestions.length === 0) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-2" data-testid="mention-suggestions">
      <span className="text-xs text-light-text/50">Suggestions:</span>
      {suggestions.map((item) => (
        <button
          key={`${item.shortType}-${item.name}`}
          type="button"
          className="inline-flex items-center gap-1 rounded-full border border-primary/30 bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary hover:bg-primary/20"
          onClick={() => onInsert(`[[${item.shortType}:${item.name}]]`)}
        >
          <span>{item.icon}</span>
          {item.name}
        </button>
      ))}
    </div>
  );
}
