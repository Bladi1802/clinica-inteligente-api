export default function AuthLayout({ title, subtitle, children }) {
  return (
    <main className="relative min-h-screen overflow-hidden bg-slate-950 text-slate-100">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(0,102,255,0.22),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(56,189,248,0.16),_transparent_24%)]" />
      <div className="relative mx-auto flex min-h-screen w-full max-w-7xl items-center justify-center px-6 py-12">
        <div className="grid w-full max-w-6xl overflow-hidden rounded-[32px] border border-slate-800 bg-slate-900/70 shadow-2xl shadow-black/30 backdrop-blur lg:grid-cols-[1.1fr_0.9fr]">
          <section className="flex flex-col justify-between border-b border-slate-800 p-10 lg:border-b-0 lg:border-r">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.35em] text-blue-400">
                Clinica Inteligente
              </p>
              <h1 className="mt-6 max-w-xl text-4xl font-bold tracking-tight text-white sm:text-5xl">
                {title}
              </h1>
              <p className="mt-6 max-w-lg text-base leading-7 text-slate-300">
                {subtitle}
              </p>
            </div>

            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                <p className="text-xs uppercase tracking-[0.25em] text-slate-500">
                  Pacientes
                </p>
                <p className="mt-2 text-sm text-slate-300">
                  Agenda y seguimiento clinico en un solo lugar.
                </p>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                <p className="text-xs uppercase tracking-[0.25em] text-slate-500">
                  Doctores
                </p>
                <p className="mt-2 text-sm text-slate-300">
                  Acceso ordenado a citas, triage y expedientes.
                </p>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                <p className="text-xs uppercase tracking-[0.25em] text-slate-500">
                  Clinic
                </p>
                <p className="mt-2 text-sm text-slate-300">
                  Control administrativo, horarios y dashboard.
                </p>
              </div>
            </div>
          </section>

          <section className="flex items-center justify-center bg-slate-950/70 p-6 sm:p-10">
            <div className="w-full max-w-md rounded-[28px] border border-slate-800 bg-slate-900/90 p-6 shadow-xl shadow-black/20 sm:p-8">
              {children}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
