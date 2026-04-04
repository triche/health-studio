import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import JournalList from "./pages/JournalList";
import JournalEdit from "./pages/JournalEdit";
import Metrics from "./pages/Metrics";
import Results from "./pages/Results";
import Goals from "./pages/Goals";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-dark-bg">
        <Sidebar />
        <div className="ml-48">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/journals" element={<JournalList />} />
            <Route path="/journals/new" element={<JournalEdit />} />
            <Route path="/journals/:id" element={<JournalEdit />} />
            <Route path="/metrics" element={<Metrics />} />
            <Route path="/results" element={<Results />} />
            <Route path="/goals" element={<Goals />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
