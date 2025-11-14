// src/App.tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import TestPage from "../src/pages/TestPage.js";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<TestPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
