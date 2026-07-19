import { logout } from "../services/api";
import { useNavigate } from "react-router-dom";
import { Activity, LogOut } from "lucide-react";

export default function Navbar({ projectName }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="bg-gray-900 border-b border-gray-700 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Activity className="text-indigo-400" size={22} />
        <span className="text-white font-bold text-lg tracking-tight">PulseBoard</span>
        {projectName && (
          <>
            <span className="text-gray-500">/</span>
            <span className="text-gray-300 text-sm">{projectName}</span>
          </>
        )}
      </div>
      <button
        onClick={handleLogout}
        className="flex items-center gap-2 text-gray-400 hover:text-white text-sm transition-colors"
      >
        <LogOut size={16} />
        Logout
      </button>
    </nav>
  );
}
