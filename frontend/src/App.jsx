import { useState, useEffect } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000";

function App() {
  const [page, setPage] = useState("review");
  const [reviewTickets, setReviewTickets] = useState([]);
  const [allTickets, setAllTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [category, setCategory] = useState("");
  const [urgency, setUrgency] = useState("");
  const [message, setMessage] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [apiOnline, setApiOnline] = useState(false);

  useEffect(() => {
    loadEverything();
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = () => {
    fetch(`${API_BASE}/health`)
      .then((r) => r.json())
      .then(() => setApiOnline(true))
      .catch(() => setApiOnline(false));
  };

  const loadEverything = () => {
    setLoading(true);
    setLoadError("");
    Promise.all([
      fetch(`${API_BASE}/tickets/needs-review`).then((r) => {
        if (!r.ok) throw new Error("Failed to load review queue");
        return r.json();
      }),
      fetch(`${API_BASE}/tickets`).then((r) => {
        if (!r.ok) throw new Error("Failed to load ticket history");
        return r.json();
      }),
    ])
      .then(([review, all]) => {
        setReviewTickets(review);
        setAllTickets(all);
        setLoading(false);
      })
      .catch((err) => {
        setLoadError(err.message);
        setLoading(false);
      });
  };

  const selectTicket = (ticket) => {
    setSelectedTicket(ticket);
    setCategory(ticket.category || "");
    setUrgency(ticket.urgency || "");
    setMessage("");
  };

  const submitCorrection = () => {
    const formData = new FormData();
    formData.append("corrected_category", category);
    formData.append("corrected_urgency", urgency);

    fetch(`${API_BASE}/tickets/${selectedTicket.id}/correct`, {
      method: "POST",
      body: formData,
    })
      .then((res) => res.json())
      .then(() => {
        setMessage(`Ticket #${selectedTicket.id} corrected.`);
        setSelectedTicket(null);
        loadEverything();
      });
  };

  const urgencyDot = { low: "bg-slate-400", medium: "bg-amber-500", high: "bg-red-500" };
  const urgencyBadge = {
    low: "bg-slate-100 text-slate-600",
    medium: "bg-amber-100 text-amber-800",
    high: "bg-red-100 text-red-700",
  };

  const categoryCounts = allTickets.reduce((acc, t) => {
    acc[t.category] = (acc[t.category] || 0) + 1;
    return acc;
  }, {});
  const urgencyCounts = allTickets.reduce((acc, t) => {
    acc[t.urgency] = (acc[t.urgency] || 0) + 1;
    return acc;
  }, {});
  const topCategory = Object.entries(categoryCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || "—";

  const filteredHistory = allTickets.filter(
    (t) =>
      t.subject?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.sender?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex min-h-screen bg-gray-50 text-gray-900">
      <aside className="w-60 bg-white border-r border-gray-200 flex flex-col">
        <div className="flex items-center gap-3 px-6 py-6 border-b border-gray-100">
          <div className="w-9 h-9 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-bold">
            T
          </div>
          <div>
            <div className="font-bold text-sm">Ticket Triage</div>
            <div className="text-xs text-gray-400">Review console</div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 flex flex-col gap-1">
          <NavItem active={page === "review"} onClick={() => setPage("review")} label={`Review Queue`} count={reviewTickets.length} />
          <NavItem active={page === "history"} onClick={() => setPage("history")} label="All Tickets" count={allTickets.length} />
        </nav>

        <div className="px-6 py-4 border-t border-gray-100 text-xs text-gray-500 flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${apiOnline ? "bg-emerald-500" : "bg-red-500"}`} />
          API {apiOnline ? "connected" : "offline"}
        </div>
      </aside>

      <main className="flex-1 px-10 py-8">
        <header className="mb-8">
          <p className="text-xs font-semibold text-indigo-600 uppercase tracking-wide mb-1">
            Support operations
          </p>
          <h1 className="text-2xl font-bold">
            {page === "review" ? "Tickets needing review" : "Ticket history"}
          </h1>
        </header>

        <div className="grid grid-cols-4 gap-4 mb-8">
          <StatCard label="Total tickets" value={allTickets.length} />
          <StatCard label="Needs review" value={reviewTickets.length} accent="text-indigo-600" />
          <StatCard label="High urgency" value={urgencyCounts.high || 0} accent="text-red-600" />
          <StatCard label="Top category" value={topCategory} small />
        </div>

        {loadError && (
          <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg mb-6">
            {loadError}. Is the API running at {API_BASE}?
          </div>
        )}

        {page === "review" && (
          <div className="grid grid-cols-5 gap-6 items-start">
            <div className="col-span-2">
              {loading && <p className="text-gray-400 text-sm">Loading...</p>}
              {!loading && reviewTickets.length === 0 && !loadError && (
                <div className="bg-white border border-dashed border-gray-200 rounded-xl p-8 text-center text-gray-400 text-sm">
                  Nothing needs review right now.
                </div>
              )}
              {message && (
                <div className="bg-emerald-50 text-emerald-800 text-sm px-4 py-2.5 rounded-lg mb-4">
                  {message}
                </div>
              )}
              <div className="flex flex-col gap-3">
                {reviewTickets.map((ticket) => (
                  <div
                    key={ticket.id}
                    onClick={() => selectTicket(ticket)}
                    className={`bg-white border rounded-xl p-4 cursor-pointer transition ${
                      selectedTicket?.id === ticket.id
                        ? "border-indigo-500 ring-2 ring-indigo-100"
                        : "border-gray-200 hover:border-gray-300 hover:shadow-sm"
                    }`}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-semibold text-gray-400">#{ticket.id}</span>
                      <span className="flex items-center gap-1.5 text-xs font-semibold text-gray-500">
                        <span className={`w-1.5 h-1.5 rounded-full ${urgencyDot[ticket.urgency]}`} />
                        {ticket.urgency}
                      </span>
                    </div>
                    <div className="font-semibold text-sm mb-2">{ticket.subject}</div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 capitalize">
                        {ticket.category}
                      </span>
                      <span className="text-xs text-gray-400">{ticket.review_reason}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="col-span-3 sticky top-8">
              {!selectedTicket && (
                <div className="border border-dashed border-gray-200 rounded-xl p-16 text-center text-gray-400 bg-white text-sm">
                  Select a ticket from the queue to review it
                </div>
              )}

              {selectedTicket && (
                <div className="bg-white border border-gray-200 rounded-xl p-7">
                  <div className="flex items-center justify-between mb-5">
                    <h2 className="text-lg font-bold">Ticket #{selectedTicket.id}</h2>
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${urgencyBadge[selectedTicket.urgency]}`}>
                      {selectedTicket.confidence} confidence
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-5 mb-5">
                    <Field label="From" value={selectedTicket.sender} />
                    <Field label="AI predicted" value={`${selectedTicket.category} / ${selectedTicket.urgency}`} />
                  </div>
                  <Field label="Subject" value={selectedTicket.subject} block />
                  <div className="mb-6">
                    <div className="text-xs uppercase tracking-wide text-gray-400 mb-1.5">Body</div>
                    <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-4 whitespace-pre-wrap leading-relaxed">
                      {selectedTicket.body}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <label className="flex flex-col gap-1.5 text-sm font-medium text-gray-600">
                      Category
                      <select
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                        className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
                      >
                        <option value="billing">billing</option>
                        <option value="technical">technical</option>
                        <option value="access">access</option>
                        <option value="general">general</option>
                      </select>
                    </label>
                    <label className="flex flex-col gap-1.5 text-sm font-medium text-gray-600">
                      Urgency
                      <select
                        value={urgency}
                        onChange={(e) => setUrgency(e.target.value)}
                        className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
                      >
                        <option value="low">low</option>
                        <option value="medium">medium</option>
                        <option value="high">high</option>
                      </select>
                    </label>
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={submitCorrection}
                      className="bg-indigo-600 text-white font-semibold text-sm px-5 py-2.5 rounded-lg hover:bg-indigo-700"
                    >
                      Submit correction
                    </button>
                    <button
                      onClick={() => setSelectedTicket(null)}
                      className="border border-gray-300 text-gray-700 text-sm font-medium px-5 py-2.5 rounded-lg hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {page === "history" && (
          <div>
            <input
              type="text"
              placeholder="Search by subject or sender..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full mb-4 border border-gray-300 rounded-lg px-4 py-2.5 text-sm bg-white"
            />
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-left text-gray-400 text-xs uppercase">
                  <tr>
                    <th className="px-5 py-3 font-semibold">ID</th>
                    <th className="px-5 py-3 font-semibold">Subject</th>
                    <th className="px-5 py-3 font-semibold">Sender</th>
                    <th className="px-5 py-3 font-semibold">Category</th>
                    <th className="px-5 py-3 font-semibold">Urgency</th>
                    <th className="px-5 py-3 font-semibold">Reviewed</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredHistory.map((t) => (
                    <tr key={t.id} className="border-t border-gray-100 hover:bg-gray-50">
                      <td className="px-5 py-3 text-gray-400">#{t.id}</td>
                      <td className="px-5 py-3 font-medium">{t.subject}</td>
                      <td className="px-5 py-3 text-gray-500">{t.sender}</td>
                      <td className="px-5 py-3 capitalize">{t.category}</td>
                      <td className="px-5 py-3">
                        <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full capitalize ${urgencyBadge[t.urgency]}`}>
                          {t.urgency}
                        </span>
                      </td>
                      <td className="px-5 py-3">{t.reviewed ? "Yes" : "No"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filteredHistory.length === 0 && (
                <p className="text-center text-gray-400 py-10 text-sm">No matching tickets.</p>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function NavItem({ active, onClick, label, count }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition ${
        active ? "bg-indigo-50 text-indigo-700" : "text-gray-600 hover:bg-gray-50"
      }`}
    >
      {label}
      <span className={`text-xs px-2 py-0.5 rounded-full ${active ? "bg-indigo-100" : "bg-gray-100"}`}>
        {count}
      </span>
    </button>
  );
}

function StatCard({ label, value, accent, small }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <div className="text-xs uppercase tracking-wide text-gray-400 mb-1.5">{label}</div>
      <div className={`font-bold ${small ? "text-base capitalize" : "text-2xl"} ${accent || "text-gray-900"}`}>
        {value}
      </div>
    </div>
  );
}

function Field({ label, value, block }) {
  return (
    <div className={block ? "mb-5" : ""}>
      <div className="text-xs uppercase tracking-wide text-gray-400 mb-1">{label}</div>
      <div className="text-sm font-medium">{value}</div>
    </div>
  );
}

export default App;
