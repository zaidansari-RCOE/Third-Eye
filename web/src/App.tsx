import { Navigate, Route, Routes } from "react-router-dom";
import { ControlRoom } from "./pages/ControlRoom";
import { DriverHud } from "./pages/DriverHud";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<ControlRoom />} />
      <Route path="/hud" element={<Navigate to="/hud/D01" replace />} />
      <Route path="/hud/:vehicleId" element={<DriverHud />} />
    </Routes>
  );
}
