import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import Documentation from './pages/Documentation'
import Console from './pages/Console'
import Analytics from './pages/Analytics'
import Sandbox from './pages/Sandbox'
import Examples from './pages/Examples'
import Changelog from './pages/Changelog'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Landing />} />
        <Route path="docs" element={<Documentation />} />
        <Route path="console" element={<Console />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="sandbox" element={<Sandbox />} />
        <Route path="examples" element={<Examples />} />
        <Route path="changelog" element={<Changelog />} />
      </Route>
    </Routes>
  )
}

export default App
