import { Route, Routes } from 'react-router-dom'
import Landing from './pages/Landing'
import WarRoom from './pages/WarRoom'
import Crisis from './pages/Crisis'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/war-room" element={<WarRoom />} />
      <Route path="/crisis" element={<Crisis />} />
      <Route path="*" element={<Landing />} />
    </Routes>
  )
}
