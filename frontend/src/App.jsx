import { useEffect, useState } from "react";
import { ArrowUpRight, ArrowLeft, Menu, X, Sun, Moon } from "lucide-react";
import Landing from "./components/Landing";
import Workspace from "./components/Workspace";
import Simulator from "./components/Simulator";
import RegulatoryV2 from "./components/RegulatoryV2";
import "./App.css";

export default function App() {
  const [route, setRoute] = useState(window.location.hash);
  const workspace = route === "#workspace";
  const simulator = route === "#simulator";
  const v2 = route.startsWith("#v2");
  const [menu, setMenu] = useState(false);
  const [theme, setTheme] = useState(document.documentElement.dataset.theme || "light");
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", theme === "dark" ? "#111413" : "#f7f6f1");
    try { localStorage.setItem("finvisors-theme", theme); } catch { /* The toggle also works when storage is unavailable. */ }
  }, [theme]);
  useEffect(() => {
    const navigate = () => {
      setRoute(window.location.hash);
      setMenu(false);
      if (["", "#workspace", "#simulator"].includes(window.location.hash) || window.location.hash.startsWith("#v2"))
        window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", navigate);
    return () => window.removeEventListener("hashchange", navigate);
  }, []);
  useEffect(() => {
    document.title = v2 ? "Regulatory research — FinVisors" : simulator ? "Regulatory Change Simulator — FinVisors" : workspace
      ? "Research workspace — FinVisors"
      : "FinVisors — Regulatory intelligence, with evidence";
  }, [workspace, simulator, v2]);

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
        <span className="header-tag">Research demo</span>
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
          {workspace || simulator || v2 ? (
            <>
              <a href="#" className="text-link"><ArrowLeft size={16} /> Overview</a>
              <a href="#workspace" aria-current={workspace ? "page" : undefined}>Company research</a>
              <a href="#v2/regulations" aria-current={v2 ? "page" : undefined}>Regulatory research</a>
            </>
          ) : (
            <>
              <a href="#approach">Our approach</a>
              <a href="#coverage">Dataset coverage</a>
              <a href="#v2/scenario">Rule simulator</a>
              <a className="button button-small" href="#v2/regulations">
                Explore regulations <ArrowUpRight size={16} />
              </a>
            </>
          )}
        </nav>
        <button className="theme-toggle icon-button" type="button"
          aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
          title={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
          onClick={() => setTheme(value => value === "dark" ? "light" : "dark")}>
          {theme === "dark" ? <Sun size={19} /> : <Moon size={19} />}
        </button>
      </header>
      <main id="main" tabIndex={-1}>
        {v2 ? <RegulatoryV2 key={route} section={route.split("/")[1] || "regulations"} /> : simulator ? <Simulator /> : workspace ? <Workspace /> : <Landing />}
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
