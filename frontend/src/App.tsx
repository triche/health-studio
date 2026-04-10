import { useEffect, useState, useCallback } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import SearchPalette from "./components/SearchPalette";
import { ToastProvider } from "./components/Toast";
import Dashboard from "./pages/Dashboard";
import JournalList from "./pages/JournalList";
import JournalEdit from "./pages/JournalEdit";
import Metrics from "./pages/Metrics";
import Results from "./pages/Results";
import Goals from "./pages/Goals";
import Timeline from "./pages/Timeline";
import Tags from "./pages/Tags";
import Settings from "./pages/Settings";
import Register from "./pages/Register";
import Login from "./pages/Login";
import { getAuthStatus, logout } from "./api/auth";

function App() {
  const [authState, setAuthState] = useState<{
    registered: boolean;
    authenticated: boolean;
    loading: boolean;
  }>({ registered: false, authenticated: false, loading: true });
  const [searchOpen, setSearchOpen] = useState(false);

  const handleSearchKeydown = useCallback((e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault();
      setSearchOpen((prev) => !prev);
    }
  }, []);

  useEffect(() => {
    window.addEventListener("keydown", handleSearchKeydown);
    return () => window.removeEventListener("keydown", handleSearchKeydown);
  }, [handleSearchKeydown]);

  const checkAuth = async () => {
    try {
      const status = await getAuthStatus();
      setAuthState({
        registered: status.registered,
        authenticated: status.authenticated,
        loading: false,
      });
    } catch {
      setAuthState({ registered: false, authenticated: false, loading: false });
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const handleLogout = async () => {
    await logout();
    setAuthState((prev) => ({ ...prev, authenticated: false }));
  };

  if (authState.loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-dark-bg">
        <div className="text-light-text/50">Loading…</div>
      </div>
    );
  }

  // Not registered — show registration
  if (!authState.registered) {
    return (
      <BrowserRouter>
        <Register onRegistered={checkAuth} />
      </BrowserRouter>
    );
  }

  // Not authenticated — show login
  if (!authState.authenticated) {
    return (
      <BrowserRouter>
        <Login onLoggedIn={checkAuth} />
      </BrowserRouter>
    );
  }

  // Authenticated — show app
  return (
    <BrowserRouter>
      <ToastProvider>
        <div className="min-h-screen bg-dark-bg text-light-text">
          <Sidebar onLogout={handleLogout} onSearchOpen={() => setSearchOpen(true)} />
          <SearchPalette open={searchOpen} onClose={() => setSearchOpen(false)} />
          <div className="pt-14 md:ml-48 md:pt-0">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/journals" element={<JournalList />} />
              <Route path="/journals/new" element={<JournalEdit />} />
              <Route path="/journals/:id" element={<JournalEdit />} />
              <Route path="/metrics" element={<Metrics />} />
              <Route path="/results" element={<Results />} />
              <Route path="/goals" element={<Goals />} />
              <Route path="/timeline" element={<Timeline />} />
              <Route path="/tags" element={<Tags />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </div>
        </div>
      </ToastProvider>
    </BrowserRouter>
  );
}

export default App;
