import { NavLink } from "react-router-dom";

const links = [
  { to: "/journals", label: "Journal" },
  { to: "/metrics", label: "Metrics" },
  { to: "/results", label: "Results" },
];

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 flex h-full w-48 flex-col bg-dark-surface p-4">
      <div className="mb-6 flex items-center gap-2">
        <img src="/logo.png" alt="" className="h-7 w-7" />
        <h2 className="text-lg font-bold text-light-text">Health Studio</h2>
      </div>
      <nav className="flex flex-col gap-1">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `rounded-lg px-3 py-2 text-sm font-medium ${
                isActive
                  ? "bg-primary text-white"
                  : "text-light-text/70 hover:bg-dark-bg hover:text-light-text"
              }`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
