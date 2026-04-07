import type { ReactNode } from "react";
import { Link } from "react-router-dom";

const MENTION_REGEX =
  /\[\[(goal|goals|metric|metrics|metric_type|exercise|exercises|exercise_type|result|results):([^\]]+)\]\]/gi;

/** Map any alias (lowercased) to canonical config key */
const ALIAS_MAP: Record<string, string> = {
  goal: "goal",
  goals: "goal",
  metric: "metric",
  metrics: "metric",
  metric_type: "metric",
  exercise: "exercise",
  exercises: "exercise",
  exercise_type: "exercise",
  result: "exercise",
  results: "exercise",
};

const TYPE_CONFIG: Record<string, { prefix: string; path: string; icon: string }> = {
  goal: { prefix: "goal", path: "/goals", icon: "🎯" },
  metric: { prefix: "metric", path: "/metrics", icon: "📊" },
  exercise: { prefix: "exercise", path: "/results", icon: "🏋️" },
};

/**
 * Parse journal content and replace [[type:name]] with styled links.
 * Returns an array of ReactNode elements.
 */
export function renderMentions(content: string): ReactNode[] {
  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  // Reset regex state
  MENTION_REGEX.lastIndex = 0;

  while ((match = MENTION_REGEX.exec(content)) !== null) {
    // Add text before this match
    if (match.index > lastIndex) {
      parts.push(content.slice(lastIndex, match.index));
    }

    const type = match[1] ? ALIAS_MAP[match[1].toLowerCase()] : undefined;
    const name = match[2];
    const config = type ? TYPE_CONFIG[type] : undefined;

    if (config) {
      parts.push(
        <Link
          key={`mention-${match.index}`}
          to={config.path}
          className="inline-flex items-center gap-1 rounded-full bg-primary/20 px-2 py-0.5 text-sm font-medium text-primary hover:bg-primary/30"
        >
          <span>{config.icon}</span>
          {name}
        </Link>,
      );
    } else {
      parts.push(match[0]);
    }

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex));
  }

  return parts;
}
