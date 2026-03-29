import { useNavigate } from "react-router-dom";
import { clearSession, getStoredUser } from "../services/auth";

export default function HomePage() {
  const navigate = useNavigate();
  const user = getStoredUser();

  function handleLogout() {
    clearSession();
    navigate("/login");
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="mx-auto flex min-h-screen w-full max-w-7xl items-center justify-center px-6 py-16">
        <div className="w-full max-w-4xl rounded-[32px] border border-slate-800 bg-slate-900/70 p-10 shadow-2xl shadow-black/30 backdrop-blur">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.3em] text-blue-400">
                Clinica Inteligente
              </p>
              <h1 className="mt-4 text-4xl font-bold tracking-tight text-white">
                Sesion iniciada
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
                Esta es una pantalla interna basica para confirmar que el login,
                la sesion y el rol ya estan funcionando desde React.
              </p>
            </div>

            <button
              type="button"
              onClick={handleLogout}
              className="rounded-2xl border border-slate-700 bg-slate-950/70 px-5 py-3 text-sm font-semibold text-white transition hover:border-red-500 hover:text-red-400"
            >
              Cerrar sesion
            </button>
          </div>

          <div className="mt-10 grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">
              <p className="text-xs uppercase tracking-[0.25em] text-slate-500">
                Usuario
              </p>
              <p className="mt-3 text-lg font-semibold text-white">
                {user?.username || "N/A"}
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">
              <p className="text-xs uppercase tracking-[0.25em] text-slate-500">
                Correo
              </p>
              <p className="mt-3 text-lg font-semibold text-white">
                {user?.email || "N/A"}
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">
              <p className="text-xs uppercase tracking-[0.25em] text-slate-500">
                Rol
              </p>
              <p className="mt-3 text-lg font-semibold text-white">
                {user?.role || "N/A"}
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
