"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

type Role = "doctor" | "nurse" | "billing_executive" | "technician" | "admin";
type Session = { userId: string; name: string; role: Role };
type Message = { id: number; from: "user" | "assistant"; text: string; route?: string; time: string };

const API_URL = process.env.NEXT_PUBLIC_API_URL || "/api";
const roleLabels: Record<Role, string> = {
  doctor: "Doctor",
  nurse: "Nurse",
  billing_executive: "Billing Executive",
  technician: "Technician",
  admin: "Administrator",
};
const roleCollections: Record<Role, { name: string; description: string; icon: string; tone: string }[]> = {
  doctor: [
    { name: "Clinical", description: "Protocols, diagnosis references & care pathways", icon: "✚", tone: "blue" },
    { name: "Pharmacy", description: "Medication formulary and prescribing guidance", icon: "✦", tone: "purple" },
    { name: "Nursing", description: "Ward procedures and patient-care standards", icon: "♡", tone: "rose" },
    { name: "General", description: "Hospital policies and everyday resources", icon: "▦", tone: "teal" },
  ],
  nurse: [
    { name: "Nursing", description: "Ward procedures and patient-care standards", icon: "♡", tone: "rose" },
    { name: "Pharmacy", description: "Medication formulary and prescribing guidance", icon: "✦", tone: "purple" },
    { name: "General", description: "Hospital policies and everyday resources", icon: "▦", tone: "teal" },
  ],
  billing_executive: [
    { name: "Billing", description: "Claims, billing codes and reimbursement policy", icon: "$", tone: "amber" },
    { name: "General", description: "Hospital policies and everyday resources", icon: "▦", tone: "teal" },
  ],
  technician: [
    { name: "Equipment", description: "Maintenance manuals and technical procedures", icon: "⌁", tone: "cyan" },
    { name: "General", description: "Hospital policies and everyday resources", icon: "▦", tone: "teal" },
  ],
  admin: [
    { name: "Clinical", description: "Protocols, diagnosis references & care pathways", icon: "✚", tone: "blue" },
    { name: "Pharmacy", description: "Medication formulary and prescribing guidance", icon: "✦", tone: "purple" },
    { name: "Nursing", description: "Ward procedures and patient-care standards", icon: "♡", tone: "rose" },
    { name: "Billing", description: "Claims, billing codes and reimbursement policy", icon: "$", tone: "amber" },
    { name: "Equipment", description: "Maintenance manuals and technical procedures", icon: "⌁", tone: "cyan" },
    { name: "General", description: "Hospital policies and everyday resources", icon: "▦", tone: "teal" },
  ],
};
const demoUsers: Record<string, { password: string; name: string; role: Role }> = {
  "dr.sarah": { password: "medibot", name: "Dr. Sarah Mitchell", role: "doctor" },
  "nurse.emma": { password: "medibot", name: "Emma Rodriguez", role: "nurse" },
  "billing.alex": { password: "medibot", name: "Alex Johnson", role: "billing_executive" },
  "tech.daniel": { password: "medibot", name: "Daniel Kim", role: "technician" },
  admin: { password: "medibot", name: "Maya Patel", role: "admin" },
};

function Icon({ children }: { children: React.ReactNode }) {
  return <span className="icon" aria-hidden="true">{children}</span>;
}

function now() {
  return new Intl.DateTimeFormat("en", { hour: "numeric", minute: "2-digit" }).format(new Date());
}

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState("");
  const [question, setQuestion] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [activeCollection, setActiveCollection] = useState("All collections");
  const [messages, setMessages] = useState<Message[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const saved = window.localStorage.getItem("mediassist-session");
    if (saved) setSession(JSON.parse(saved) as Session);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  const collections = useMemo(() => session ? roleCollections[session.role] : [], [session]);
  const login = (event: FormEvent) => {
    event.preventDefault();
    const account = demoUsers[userId.trim().toLowerCase()];
    if (!account || account.password !== password) {
      setLoginError("We couldn’t verify those credentials. Check your User ID and password.");
      return;
    }
    const next = { userId: userId.trim(), name: account.name, role: account.role };
    window.localStorage.setItem("mediassist-session", JSON.stringify(next));
    setSession(next);
    setLoginError("");
    setMessages([]);
  };

  const signOut = () => {
    window.localStorage.removeItem("mediassist-session");
    setSession(null);
    setPassword("");
    setMessages([]);
  };

  const sendMessage = async (event?: FormEvent, value?: string) => {
    event?.preventDefault();
    const text = (value ?? question).trim();
    if (!text || !session || isSending) return;
    setQuestion("");
    setMessages((current) => [...current, { id: Date.now(), from: "user", text, time: now() }]);
    setIsSending(true);
    try {
      const response = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text, role: session.role }),
      });
      if (!response.ok) throw new Error(`Request failed (${response.status})`);
      const data = await response.json() as { answer: string; route: string };
      setMessages((current) => [...current, { id: Date.now() + 1, from: "assistant", text: data.answer, route: data.route, time: now() }]);
    } catch {
      setMessages((current) => [...current, {
        id: Date.now() + 1,
        from: "assistant",
        text: "I’m unable to reach the MediAssist service right now. Please confirm the FastAPI server is running and try again.",
        route: "connection-error",
        time: now(),
      }]);
    } finally {
      setIsSending(false);
    }
  };

  if (!session) {
    return (
      <main className="login-shell">
        <section className="login-art">
          <div className="brand"><div className="brand-mark">✚</div><span>MediAssist</span></div>
          <div className="art-copy">
            <span className="eyebrow">INTELLIGENCE FOR BETTER CARE</span>
            <h1>Every answer,<br /><em>closer to care.</em></h1>
            <p>A secure knowledge companion for the people who keep healthcare moving.</p>
          </div>
          <div className="art-footer"><span className="pulse-dot" /> All systems operational <span>•</span> HIPAA-conscious workspace</div>
          <div className="orb orb-one" /><div className="orb orb-two" />
        </section>
        <section className="login-panel">
          <div className="login-card">
            <div className="mobile-brand"><div className="brand-mark">✚</div><span>MediAssist</span></div>
            <span className="eyebrow">WELCOME BACK</span>
            <h2>Sign in to your workspace</h2>
            <p className="muted">Use your MediAssist credentials to continue.</p>
            <form onSubmit={login} className="login-form">
              <label>User ID<input value={userId} onChange={(e) => setUserId(e.target.value)} placeholder="e.g. dr.sarah" autoComplete="username" required /></label>
              <label>Password
                <span className="password-wrap"><input type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" autoComplete="current-password" required /><button type="button" onClick={() => setShowPassword(!showPassword)} aria-label="Toggle password visibility">{showPassword ? "Hide" : "Show"}</button></span>
              </label>
              {loginError && <div className="form-error"><Icon>!</Icon>{loginError}</div>}
              <button className="primary-button" type="submit">Sign in <span>→</span></button>
            </form>
            <div className="demo-hint"><strong>Demo access</strong><span>User ID: <code>dr.sarah</code> · Password: <code>medibot</code></span></div>
            <p className="security-note"><Icon>⌁</Icon> Your session is protected with role-based access controls.</p>
          </div>
          <div className="login-bottom">© 2025 MediAssist <span>•</span> Privacy <span>•</span> Help center</div>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">✚</div><span>MediAssist</span></div>
        <div className="workspace-label">WORKSPACE</div>
        <button className="new-chat" onClick={() => setMessages([])}><Icon>＋</Icon> New conversation <span>⌘ K</span></button>
        <div className="side-section"><div className="section-title">Your collections <span>{collections.length}</span></div>{collections.map((item) => <button key={item.name} className={`collection-link ${activeCollection === item.name ? "selected" : ""}`} onClick={() => setActiveCollection(item.name)}><span className={`mini-icon ${item.tone}`}>{item.icon}</span>{item.name}<span className="arrow">›</span></button>)}</div>
        <div className="sidebar-bottom"><div className="support-card"><span className="support-icon">?</span><div><strong>Need a hand?</strong><small>Visit the help center</small></div><span>↗</span></div><div className="profile"><div className="avatar">{session.name.split(" ").map((part) => part[0]).join("").slice(0, 2)}</div><div className="profile-copy"><strong>{session.name}</strong><small>{roleLabels[session.role]}</small></div><button onClick={signOut} aria-label="Sign out" title="Sign out">⇥</button></div></div>
      </aside>
      <section className="chat-area">
        <header className="topbar"><div><span className="status-label"><span className="pulse-dot" /> MediAssist online</span><h2>Knowledge assistant</h2></div><div className="top-actions"><button className="icon-button" title="Notifications">♢<span className="notification-dot" /></button><button className="avatar top-avatar" onClick={signOut}>{session.name.split(" ").map((part) => part[0]).join("").slice(0, 2)}</button></div></header>
        <div className="chat-content">
          {messages.length === 0 ? <div className="welcome"><div className="welcome-icon">✦</div><span className="eyebrow">YOUR SECURE KNOWLEDGE SPACE</span><h1>How can I help, <em>{session.name.split(" ")[0]}?</em></h1><p>Ask about policies, clinical protocols, medications, equipment, or operational data. I’ll find the answer from the collections available to your role.</p><div className="quick-grid">{[["Clinical guidance", "What are the first steps in the sepsis protocol?", "✚"], ["Medication lookup", "What are the storage requirements for insulin?", "✦"], ["My access", "Which resources can I access?", "⌁"]].map(([title, prompt, icon]) => <button key={title} className="quick-card" onClick={() => sendMessage(undefined, prompt)}><span>{icon}</span><strong>{title}</strong><small>{prompt}</small><b>→</b></button>)}</div></div> : <div className="message-list">{messages.map((message) => <div key={message.id} className={`message-row ${message.from}`}><div className={`message-avatar ${message.from}`}>{message.from === "assistant" ? "✦" : session.name.split(" ").map((part) => part[0]).join("").slice(0, 2)}</div><div className="message-body"><div className="message-meta"><strong>{message.from === "assistant" ? "MediAssist" : "You"}</strong><span>{message.time}</span>{message.route && <span className="route-tag">{message.route}</span>}</div><div className="message-bubble">{message.text}</div></div></div>)}{isSending && <div className="message-row assistant"><div className="message-avatar assistant">✦</div><div className="message-body"><div className="message-meta"><strong>MediAssist</strong><span>thinking…</span></div><div className="message-bubble typing"><i /><i /><i /></div></div></div>}<div ref={bottomRef} /></div>}
          <div className="composer-wrap"><div className="active-context"><span className="context-dot" /> Searching <strong>{activeCollection}</strong> <button onClick={() => setActiveCollection("All collections")}>×</button></div><form className="composer" onSubmit={sendMessage}><textarea value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void sendMessage(); } }} placeholder="Ask MediAssist anything…" rows={1} /><div className="composer-tools"><button type="button" title="Attach a file">＋</button><span>Shift + Enter for new line</span><button className="send-button" type="submit" disabled={!question.trim() || isSending} aria-label="Send message">↑</button></div></form><small className="disclaimer">MediAssist can make mistakes. Verify critical information with official clinical resources.</small></div>
        </div>
      </section>
    </main>
  );
}
