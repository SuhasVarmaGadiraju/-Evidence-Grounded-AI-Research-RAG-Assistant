import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Chat from './pages/Chat';
import Upload from './pages/Upload';
import Documents from './pages/Documents';
import Settings from './pages/Settings';
import QueryTest from './pages/QueryTest';
import SemanticSearch from './pages/SemanticSearch';
import BM25Search from './pages/BM25Search';
import HybridSearch from './pages/HybridSearch';
import RerankSearch from './pages/RerankSearch';
import PromptBuilder from './pages/PromptBuilder';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="chat" element={<Chat />} />
          <Route path="upload" element={<Upload />} />
          <Route path="documents" element={<Documents />} />
          <Route path="query-test" element={<QueryTest />} />
          <Route path="semantic-search" element={<SemanticSearch />} />
          <Route path="bm25-search" element={<BM25Search />} />
          <Route path="hybrid-search" element={<HybridSearch />} />
          <Route path="rerank-search" element={<RerankSearch />} />
          <Route path="prompt-builder" element={<PromptBuilder />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
