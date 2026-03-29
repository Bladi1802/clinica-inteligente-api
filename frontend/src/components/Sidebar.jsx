import { Link, useLocation } from "react-router-dom";

const navByRole = {
  PATIENT: [
    { label: "Dashboard", to: "/patient" },
    { label: "Citas", to: "/patient" },
    { label: "Perfil", to: "/patient" },
  ],
  DOCTOR: [
    { label: "Dashboard", to: "/doctor" },
    { label: "Agenda", to: "/doctor" },
    { label: "Pacientes", to: "/doctor" },
  ],
  CLINIC: [
    { label: "Dashboard", to: "/clinic" },
    { label: "Doctores", to: "/clinic" },
    { label: "Pacientes", to: "/clinic" },
    { label: "Servicios", to: "/clinic" },
  ],
};

export default function Sidebar({ role }) {
  const location = useLocation();
  const items = navByRole[role] || [];

  return (
    <aside className="flex h-full w-full max-w-xs flex-col border-r border-slate-800 bg-slate-950/90 p-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.35em] text-blue-400">
          Clinica
        </p>
        <h2 className="mt-4 text-2xl font-bold text-white">Inteligente</h2>
        <p className="mt-2 text-sm text-slate-400">
          Panel interno para {role || "usuario"}.
        </p>
      </div>

      <nav className="mt-10 space-y-2">
        {items.map((item) => {
          const active = location.pathname === item.to;

          return (
            <Link
              key={`${role}-${item.label}`}
              to={item.to}
              className={`block rounded-2xl px-4 py-3 text-sm font-medium transition ${
                active
                  ? "bg-blue-600 text-white"
                  : "text-slate-300 hover:bg-slate-900 hover:text-white"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
