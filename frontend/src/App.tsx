import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import JournalList from "./pages/JournalList";
import JournalEdit from "./pages/JournalEdit";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-dark-bg">
        <Routes>
          <Route path="/" element={<Navigate to="/journals" replace />} />
          <Route path="/journals" element={<JournalList />} />
          <Route path="/journals/new" element={<JournalEdit />} />
          <Route path="/journals/:id" element={<JournalEdit />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
