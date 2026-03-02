import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { BatchDetail } from '@/pages/BatchDetail'
import { Leaderboard } from '@/pages/Leaderboard'
import { ModelComparison } from '@/pages/ModelComparison'
import { PromptDetail } from '@/pages/PromptDetail'
import { PromptsList } from '@/pages/PromptsList'
import { ResultDetail } from '@/pages/ResultDetail'
import { OllamaModels } from '@/pages/OllamaModels'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/batches/:id" element={<BatchDetail />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/models" element={<ModelComparison />} />
          <Route path="/prompts" element={<PromptsList />} />
          <Route path="/prompts/:id" element={<PromptDetail />} />
          <Route path="/results/:id" element={<ResultDetail />} />
          <Route path="/ollama" element={<OllamaModels />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
