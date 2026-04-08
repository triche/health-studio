import { Link } from "react-router-dom";

interface TagListProps {
  tags: string[];
  baseUrl?: string;
}

export default function TagList({ tags, baseUrl = "/tags" }: TagListProps) {
  if (tags.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1.5">
      {tags.map((tag) => (
        <Link
          key={tag}
          to={`${baseUrl}?tag=${encodeURIComponent(tag)}`}
          className="inline-block rounded-full bg-primary/20 px-2 py-0.5 text-xs font-medium text-primary hover:bg-primary/30"
        >
          {tag}
        </Link>
      ))}
    </div>
  );
}
