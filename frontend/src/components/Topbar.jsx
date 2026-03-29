export default function Topbar({ title, user, onLogout }) {
  return (
    <header className="flex flex-col gap-4 border-b border-slate-800 bg-slate-900/60 px-6 py-5 backdrop-blur sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-slate-500">
          Panel
        </p>
        <h1 className="mt-2 text-2xl font-bold text-white">{title}</h1>
      </div>

      <div className="flex items-center gap-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3 text-right">
          <p className="text-sm font-semibold text-white">{user?.username || "N/A"}</p>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
            {user?.role || "N/A"}
          </p>
        </div>

        <button
          type="button"
          onClick={onLogout}
          className="rounded-2xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm font-semibold text-white transition hover:border-red-500 hover:text-red-400"
        >
          Salir
        </button>
      </div>
    </header>
  );
}
