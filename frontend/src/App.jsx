import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { login, register, getProjects, createProject } from "./services/api";
import Navbar from "./components/Navbar";
import Dashboard from "./components/Dashboard";
import { Activity, Plus } from "lucide-react";

// ── Auth Page ──────────────────────────────────────────────────────────────
function AuthPage() {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      if (mode === "register") await register(email, password);
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong");
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-2 mb-8">
          <Activity className="text-indigo-400" size={28} />
          <span className="text-white text-2xl font-bold">PulseBoard</span>
        </div>
        <div className="bg-gray-900 rounded-2xl p-8 border border-gray-700">
          <h2 className="text-white text-xl font-semibold mb-6">
            {mode === "login" ? "Sign in" : "Create account"}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-gray-800 text-white rounded-lg px-4 py-3 border border-gray-600 focus:outline-none focus:border-indigo-500 placeholder-gray-500"
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-gray-800 text-white rounded-lg px-4 py-3 border border-gray-600 focus:outline-none focus:border-indigo-500 placeholder-gray-500"
              required
            />
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <button
              type="submit"
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3 rounded-lg transition-colors"
            >
              {mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>
          <p className="text-gray-400 text-sm text-center mt-4">
            {mode === "login" ? "No account? " : "Already have one? "}
            <button
              onClick={() => setMode(mode === "login" ? "register" : "login")}
              className="text-indigo-400 hover:text-indigo-300"
            >
              {mode === "login" ? "Register" : "Sign in"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Project selector ───────────────────────────────────────────────────────
function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [selected, setSelected] = useState(null);
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    getProjects().then((r) => {
      setProjects(r.data);
      if (r.data.length > 0) setSelected(r.data[0]);
    });
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    const res = await createProject(newName.trim());
    setProjects((p) => [...p, res.data]);
    setSelected(res.data);
    setNewName("");
    setCreating(false);
  };

  if (!localStorage.getItem("pb_token")) return <Navigate to="/login" />;

  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar projectName={selected?.name} />
      <div className="flex h-[calc(100vh-57px)]">
        {/* Sidebar */}
        <aside className="w-56 bg-gray-900 border-r border-gray-700 p-4 flex flex-col gap-1">
          <p className="text-gray-500 text-xs uppercase tracking-wider mb-2 px-2">Projects</p>
          {projects.map((p) => (
            <button
              key={p.id}
              onClick={() => setSelected(p)}
              className={`text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                selected?.id === p.id
                  ? "bg-indigo-600 text-white"
                  : "text-gray-300 hover:bg-gray-800"
              }`}
            >
              {p.name}
            </button>
          ))}
          {creating ? (
            <form onSubmit={handleCreate} className="mt-2">
              <input
                autoFocus
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Project name"
                className="w-full bg-gray-800 text-white text-sm rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:border-indigo-500 placeholder-gray-500"
              />
              <div className="flex gap-2 mt-2">
                <button type="submit" className="text-xs bg-indigo-600 text-white px-3 py-1 rounded-lg">
                  Create
                </button>
                <button
                  type="button"
                  onClick={() => setCreating(false)}
                  className="text-xs text-gray-400 hover:text-white"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <button
              onClick={() => setCreating(true)}
              className="flex items-center gap-2 text-gray-500 hover:text-gray-300 text-sm px-3 py-2 mt-2 transition-colors"
            >
              <Plus size={14} />
              New project
            </button>
          )}
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto">
          {selected ? (
            <Dashboard project={selected} />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              Create a project to get started
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

// ── App root ───────────────────────────────────────────────────────────────
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<AuthPage />} />
        <Route path="/" element={<ProjectsPage />} />
      </Routes>
    </BrowserRouter>
  );
}
