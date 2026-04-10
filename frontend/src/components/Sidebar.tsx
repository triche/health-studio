import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import DarkModeToggle from "./DarkModeToggle";

const links = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/timeline", label: "Timeline" },
  { to: "/journals", label: "Journal" },
  { to: "/metrics", label: "Metrics" },
  { to: "/results", label: "Results" },
  { to: "/goals", label: "Goals" },
  { to: "/tags", label: "Tags" },
];

interface SidebarProps {
  onLogout?: () => void;
  onSearchOpen?: () => void;
}

export default function Sidebar({ onLogout, onSearchOpen }: SidebarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();

  const navContent = (
    <>
      <div className="mb-6 flex items-center gap-2">
        <img src="/logo.png" alt="" className="h-7 w-7" />
        <h2 className="text-lg font-bold text-slate-100">Health Studio</h2>
      </div>
      <nav className="flex flex-1 flex-col gap-1">
        {onSearchOpen && (
          <button
            onClick={() => {
              setMobileOpen(false);
              onSearchOpen();
            }}
            className="mb-2 flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-slate-100"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            Search
            <kbd className="ml-auto rounded bg-slate-700 px-1.5 py-0.5 text-[10px] text-slate-500">
              ⌘K
            </kbd>
          </button>
        )}
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              `rounded-lg px-3 py-2 text-sm font-medium ${
                isActive
                  ? "bg-primary text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
              }`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto flex items-center justify-center gap-1 border-t border-slate-700 pt-3">
        {/* Settings */}
        <button
          aria-label="Settings"
          onClick={() => {
            setMobileOpen(false);
            navigate("/settings");
          }}
          className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-100"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
        </button>
        {/* Dark mode toggle */}
        <DarkModeToggle />
        {/* Logout */}
        {onLogout && (
          <button
            aria-label="Sign out"
            onClick={onLogout}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-100"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3-3l3-3m0 0l-3-3m3 3H9"
              />
            </svg>
          </button>
        )}
      </div>
    </>
  );

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        aria-label="Open menu"
        onClick={() => setMobileOpen(true)}
        className="fixed left-3 top-3 z-40 rounded-lg bg-slate-800 p-2 text-slate-400 hover:text-slate-100 md:hidden"
      >
        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </button>

      {/* Desktop sidebar */}
      <aside className="fixed left-0 top-0 hidden h-full w-48 flex-col bg-[#1E293B] p-4 md:flex">
        {navContent}
      </aside>

      {/* Mobile overlay + drawer */}
      {mobileOpen && (
        <>
          <div
            data-testid="sidebar-overlay"
            className="fixed inset-0 z-40 bg-black/50 md:hidden"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="fixed left-0 top-0 z-50 flex h-full w-64 flex-col bg-[#1E293B] p-4 md:hidden">
            <button
              aria-label="Close menu"
              onClick={() => setMobileOpen(false)}
              className="mb-2 self-end rounded-lg p-1 text-slate-400 hover:text-slate-100"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
            {navContent}
          </aside>
        </>
      )}
    </>
  );
}
