import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Classify from './pages/Classify'
import Search from './pages/Search'
import Ask from './pages/Ask'
import ModelPerformance from './pages/ModelPerformance'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="classify" element={<Classify />} />
          <Route path="search" element={<Search />} />
          <Route path="ask" element={<Ask />} />
          <Route path="performance" element={<ModelPerformance />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
