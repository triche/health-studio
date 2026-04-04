import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import JournalList from "./pages/JournalList";
import JournalEdit from "./pages/JournalEdit";
import Metrics from "./pages/Metrics";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-dark-bg">
        <Sidebar />
        <div className="ml-48">
          <Routes>
            <Route path="/" element={<Navigate to="/journals" replace />} />
            <Route path="/journals" element={<JournalList />} />
            <Route path="/journals/new" element={<JournalEdit />} />
            <Route path="/journals/:id" element={<JournalEdit />} />
            <Route path="/metrics" element={<Metrics />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
