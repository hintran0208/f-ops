import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import PipelineModule from './modules/PipelineModule'
import InfrastructureModule from './modules/InfrastructureModule'
import KBConnectModule from './modules/KBConnectModule'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<PipelineModule />} />
          <Route path="/pipeline" element={<PipelineModule />} />
          <Route path="/infrastructure" element={<InfrastructureModule />} />
          <Route path="/kb" element={<KBConnectModule />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App