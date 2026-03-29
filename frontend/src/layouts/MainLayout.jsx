import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";
import { clearSession, getStoredUser } from "../services/auth";

export default function MainLayout({ title, children }) {
  const navigate = useNavigate();
  const user = getStoredUser();

  function handleLogout() {
    clearSession();
    navigate("/login");
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="grid min-h-screen lg:grid-cols-[280px_1fr]">
        <Sidebar role={user?.role} />

        <div className="flex min-h-screen flex-col">
          <Topbar title={title} user={user} onLogout={handleLogout} />

          <section className="flex-1 px-6 py-6">
            <div className="mx-auto w-full max-w-6xl">{children}</div>
          </section>
        </div>
      </div>
    </main>
  );
}
