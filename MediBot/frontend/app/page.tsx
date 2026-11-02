"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

type Role = "doctor" | "nurse" | "billing_executive" | "technician" | "admin";
type Session = { userId: string; name: string; role: Role; token: string };
type Message = { id: number; from: "user" | "assistant"; text: string; route?: string; time: string };

// Make sure your backend FastAPI is running on this URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const roleLabels: Record<Role, string> = {
  doctor: "Doctor",
  nurse: "Nurse",
  billing_executive: "Billing Executive",
  technician: "Technician",
  admin: "Administrator",
};

const roleCollections: Record<Role, { name: string; description: string; icon: string; tone: string }[]> = {
  doctor: [
    { name: "clinical", description: "Protocols, diagnosis references", icon: "✚", tone: "blue" },
    { name: "pharmacy", description: "Medication formulary", icon: "✦", tone: "purple" },
    { name: "nursing", description: "Ward procedures", icon: "♡", tone: "rose" },
    { name: "general", description: "Hospital policies", icon: "▦", tone: "teal" },
  ],
  nurse: [
    { name: "nursing", description: "Ward procedures", icon: "♡", tone: "rose" },
    { name: "pharmacy", description: "Medication formulary", icon: "✦", tone: "purple" },
    { name: "general", description: "Hospital policies", icon: "▦", tone: "teal" },
  ],
  billing_executive: [
    { name: "billing", description: "Claims, billing codes", icon: "$", tone: "amber" },
    { name: "general", description: "Hospital policies", icon: "▦", tone: "teal" },
  ],
  technician: [
    { name: "equipment", description: "Maintenance manuals", icon: "⌁", tone: "cyan" },
    { name: "general", description: "Hospital policies", icon: "▦", tone: "teal" },
  ],
  admin: [
    { name: "clinical", description: "Protocols", icon: "✚", tone: "blue" },
    { name: "pharmacy", description: "Medication", icon: "✦", tone: "purple" },
    { name: "nursing", description: "Ward procedures", icon: "♡", tone: "rose" },
    { name: "billing", description: "Claims", icon: "$", tone: "amber" },
    { name: "equipment", description: "Maintenance", icon: "⌁", tone: "cyan" },
    { name: "general", description: "Hospital policies", icon: "▦", tone: "teal" },
  ],
};

// Helper function to decode the JWT Token in the browser
function parseJwt(token: string) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

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
  const [activeCollection, setActiveCollection] = useState("general");
  const [messages, setMessages] = useState<Message[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const saved = window.localStorage.getItem("mediassist-session");
    if (saved) {
      const parsedSession = JSON.parse(saved) as Session;
      // Optional: Check if token is expired here, for now just load it
      setSession(parsedSession);
    }
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  const collections = useMemo(() => session ? roleCollections[session.role] : [], [session]);

  const login = async (event: FormEvent) => {
    event.preventDefault();
    setLoginError("");

    // FastAPI OAuth2 requires Form Data, not JSON
    const formData = new URLSearchParams();
    formData.append("username", userId.trim().toLowerCase());
    formData.append("password", password);

    try {
      const response = await fetch(`${API_URL}/api/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
      });

      if (!response.ok) {
        setLoginError("We couldn’t verify those credentials. Check your User ID and password.");
        return;
      }

      const data = await response.json();
      const decodedToken = parseJwt(data.access_token);

      if (!decodedToken) throw new Error("Invalid token received");

      // Save token and user data to session
      const nextSession: Session = {
        userId: decodedToken.sub,
        name: decodedToken.sub.replace("_", " ").toUpperCase(),
        role: decodedToken.role as Role,
        token: data.access_token
      };

      window.localStorage.setItem("mediassist-session", JSON.stringify(nextSession));
      setSession(nextSession);
      setActiveCollection("general");
      setMessages([]);
    } catch (error) {
      console.error(error);
      setLoginError("Could not connect to the authentication server.");
    }
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
      // ----------------------------------------------------------------------
      // UPDATED CHAT FETCH: Points to the new API router endpoint and
      // passes the exact payload structure your chat_router.py expects!
      // ----------------------------------------------------------------------
      const response = await fetch(`${API_URL}/api/retrieval/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.token}`
        },
        body: JSON.stringify({
          question: text,               // CHANGED: 'question' instead of 'query'
          collection: activeCollection  // CHANGED: 'collection' instead of 'active_collection'
        })
      });

      if (response.status === 401) {
        alert("Your session has expired. Please log in again.");
        signOut();
        return;
      }

      if (response.status === 403) {
        setMessages((current) => [...current, {
          id: Date.now() + 1,
          from: "assistant",
          text: `Access Denied: Your role (${roleLabels[session.role]}) does not have permission to query the ${activeCollection} collection.`,
          route: "rbac-error",
          time: now(),
        }]);
        return;
      }

      if (!response.ok) throw new Error(`Request failed (${response.status})`);

      const data = await response.json();
      setMessages((current) => [...current, {
        id: Date.now() + 1,
        from: "assistant",
        text: data.answer || data.message || "Query successful.",
        route: activeCollection,
        time: now()
      }]);

    } catch (error) {
      setMessages((current) => [...current, {
        id: Date.now() + 1,
        from: "assistant",
        text: "I’m unable to reach the MediAssist backend right now. Please confirm the FastAPI server is running and try again.",
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
              <label>User ID<input value={userId} onChange={(e) => setUserId(e.target.value)} placeholder="e.g. doc_john" autoComplete="username" required /></label>
              <label>Password
                <span className="password-wrap"><input type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" autoComplete="current-password" required /><button type="button" onClick={() => setShowPassword(!showPassword)} aria-label="Toggle password visibility">{showPassword ? "Hide" : "Show"}</button></span>
              </label>
              {loginError && <div className="form-error"><Icon>!</Icon>{loginError}</div>}
              <button className="primary-button" type="submit">Sign in <span>→</span></button>
            </form>
            <div className="demo-hint"><strong>Demo Users</strong><span>Doc: <code>doc_john</code> | Nurse: <code>nurse_joy</code> | Billing: <code>bill_smith</code><br/>Password for all: <code>password123</code></span></div>
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
        <div className="side-section">
          <div className="section-title">Your collections <span>{collections.length}</span></div>
          {collections.map((item) => (
            <button
              key={item.name}
              className={`collection-link ${activeCollection === item.name ? "selected" : ""}`}
              onClick={() => setActiveCollection(item.name)}
            >
              <span className={`mini-icon ${item.tone}`}>{item.icon}</span>
              {item.name}
              <span className="arrow">›</span>
            </button>
          ))}
        </div>
        <div className="sidebar-bottom">
          <div className="support-card"><span className="support-icon">?</span><div><strong>Need a hand?</strong><small>Visit the help center</small></div><span>↗</span></div>
          <div className="profile">
            <div className="avatar">{session.name.slice(0, 2)}</div>
            <div className="profile-copy"><strong>{session.name}</strong><small>{roleLabels[session.role]}</small></div>
            <button onClick={signOut} aria-label="Sign out" title="Sign out">⇥</button>
          </div>
        </div>
      </aside>
      <section className="chat-area">
        <header className="topbar">
          <div><span className="status-label"><span className="pulse-dot" /> MediAssist online</span><h2>Knowledge assistant</h2></div>
          <div className="top-actions"><button className="icon-button" title="Notifications">♢<span className="notification-dot" /></button><button className="avatar top-avatar" onClick={signOut}>{session.name.slice(0, 2)}</button></div>
        </header>
        <div className="chat-content">
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-icon">✦</div>
              <span className="eyebrow">YOUR SECURE KNOWLEDGE SPACE</span>
              <h1>How can I help, <em>{session.name.split(" ")[0]}?</em></h1>
              <p>Ask about policies, clinical protocols, medications, equipment, or operational data. I’ll find the answer from the collections available to your role.</p>
              <div className="quick-grid">
                {[["Clinical guidance", "What are the first steps in the sepsis protocol?", "✚"], ["Medication lookup", "What are the storage requirements for insulin?", "✦"], ["My access", "Which resources can I access?", "⌁"]].map(([title, prompt, icon]) => (
                  <button key={title} className="quick-card" onClick={() => sendMessage(undefined, prompt)}>
                    <span>{icon}</span><strong>{title}</strong><small>{prompt}</small><b>→</b>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="message-list">
              {messages.map((message) => (
                <div key={message.id} className={`message-row ${message.from}`}>
                  <div className={`message-avatar ${message.from}`}>{message.from === "assistant" ? "✦" : session.name.slice(0, 2)}</div>
                  <div className="message-body">
                    <div className="message-meta"><strong>{message.from === "assistant" ? "MediAssist" : "You"}</strong><span>{message.time}</span>{message.route && <span className="route-tag">{message.route}</span>}</div>
                    <div className="message-bubble">{message.text}</div>
                  </div>
                </div>
              ))}
              {isSending && (
                <div className="message-row assistant">
                  <div className="message-avatar assistant">✦</div>
                  <div className="message-body">
                    <div className="message-meta"><strong>MediAssist</strong><span>thinking…</span></div>
                    <div className="message-bubble typing"><i /><i /><i /></div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
          <div className="composer-wrap">
            <div className="active-context"><span className="context-dot" /> Searching <strong>{activeCollection}</strong></div>
            <form className="composer" onSubmit={sendMessage}>
              <textarea value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void sendMessage(); } }} placeholder="Ask MediAssist anything…" rows={1} />
              <div className="composer-tools">
                <button type="button" title="Attach a file">＋</button><span>Shift + Enter for new line</span>
                <button className="send-button" type="submit" disabled={!question.trim() || isSending} aria-label="Send message">↑</button>
              </div>
            </form>
            <small className="disclaimer">MediAssist can make mistakes. Verify critical information with official clinical resources.</small>
          </div>
        </div>
      </section>
    </main>
  );
}