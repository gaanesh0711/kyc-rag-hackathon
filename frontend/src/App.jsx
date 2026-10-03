import { useEffect, useState } from "react";
import { ArrowUpRight, ArrowLeft, Menu, X } from "lucide-react";
import Landing from "./components/Landing";
import Workspace from "./components/Workspace";
import "./App.css";

export default function App() {
  const [workspace, setWorkspace] = useState(
    window.location.hash === "#workspace",
  );
  const [menu, setMenu] = useState(false);
  useEffect(() => {
    const navigate = () => {
      if (window.location.hash === "#workspace") setWorkspace(true);
      else if (!window.location.hash) setWorkspace(false);
      setMenu(false);
      if (["", "#workspace"].includes(window.location.hash))
        window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", navigate);
    return () => window.removeEventListener("hashchange", navigate);
  }, []);
  useEffect(() => {
    document.title = workspace
      ? "Research workspace — FinVisors"
      : "FinVisors — Regulatory intelligence, with evidence";
  }, [workspace]);

  return (
    <>
      <a
        className="skip-link"
        href="#main"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("main").focus();
        }}
      >
        Skip to content
      </a>
      <header className="site-header">
        <a href="#" className="wordmark" aria-label="FinVisors home">
          <span className="logo-mark" aria-hidden="true">
            f<span>v</span>
          </span>
          FinVisors<span className="wordmark-dot">.</span>
        </a>
        <span className="header-divider" aria-hidden="true" />
        <span className="header-tag">Regulatory intelligence</span>
        <button
          className="menu-toggle icon-button"
          aria-label={menu ? "Close navigation" : "Open navigation"}
          aria-expanded={menu}
          onClick={() => setMenu(!menu)}
        >
          {menu ? <X size={20} /> : <Menu size={20} />}
        </button>
        <nav
          className={menu ? "header-nav open" : "header-nav"}
          aria-label="Main navigation"
        >
          {workspace ? (
            <a href="#" className="text-link">
              <ArrowLeft size={16} /> Overview
            </a>
          ) : (
            <>
              <a href="#approach">Our approach</a>
              <a href="#coverage">Dataset coverage</a>
              <a className="button button-small" href="#workspace">
                Open workspace <ArrowUpRight size={16} />
              </a>
            </>
          )}
        </nav>
      </header>
      <main id="main" tabIndex={-1}>
        {workspace ? <Workspace /> : <Landing />}
      </main>
      <footer className="site-footer">
        <a href="#" className="footer-brand">
          FinVisors.
        </a>
        <p>Clarity for the people behind the review.</p>
        <span>Public research demo · Dataset-grounded answers</span>
      </footer>
    </>
  );
}
