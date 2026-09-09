import { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [category, setCategory] = useState("");
  const [urgency, setUrgency] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchTickets();
  }, []);

  const fetchTickets = () => {
    setLoading(true);
    fetch("http://localhost:8000/tickets/needs-review")
      .then((res) => res.json())
      .then((data) => {
        setTickets(data);
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

    fetch(`http://localhost:8000/tickets/${selectedTicket.id}/correct`, {
      method: "POST",
      body: formData,
    })
      .then((res) => res.json())
      .then(() => {
        setMessage(`Ticket #${selectedTicket.id} corrected.`);
        setSelectedTicket(null);
        fetchTickets();
      });
  };

  const urgencyStyles = {
    low: "bg-slate-100 text-slate-600",
    medium: "bg-amber-100 text-amber-800",
    high: "bg-red-100 text-red-800",
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-5xl mx-auto px-6 py-10">
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Ticket Review Queue</h1>
          <p className="text-gray-500 mt-1">
            Tickets flagged for low confidence or spot-checked at random
          </p>
        </header>

        <div className="grid grid-cols-2 gap-6 items-start">
          <div>
            {loading && <p className="text-gray-500">Loading...</p>}
            {!loading && tickets.length === 0 && (
              <p className="text-gray-500">Nothing needs review right now.</p>
            )}
            {message && (
              <div className="bg-emerald-50 text-emerald-800 text-sm px-4 py-2 rounded-lg mb-4">
                {message}
              </div>
            )}

            <div className="flex flex-col gap-3">
              {tickets.map((ticket) => (
                <div
                  key={ticket.id}
                  onClick={() => selectTicket(ticket)}
                  className={`bg-white border rounded-xl p-4 cursor-pointer transition ${
                    selectedTicket?.id === ticket.id
                      ? "border-indigo-500 ring-2 ring-indigo-100"
                      : "border-gray-200 hover:border-gray-400"
                  }`}
                >
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-semibold text-gray-500">#{ticket.id}</span>
                    <span
                      className={`text-xs font-semibold px-2.5 py-0.5 rounded-full capitalize ${urgencyStyles[ticket.urgency]}`}
                    >
                      {ticket.urgency}
                    </span>
                  </div>
                  <div className="font-semibold text-gray-900 mb-2">{ticket.subject}</div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700 capitalize">
                      {ticket.category}
                    </span>
                    <span className="text-xs text-gray-400">{ticket.review_reason}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="sticky top-6">
            {!selectedTicket && (
              <div className="border border-dashed border-gray-300 rounded-xl p-10 text-center text-gray-400 bg-white">
                Select a ticket to review its details
              </div>
            )}

            {selectedTicket && (
              <div className="bg-white border border-gray-200 rounded-xl p-6">
                <h2 className="text-lg font-bold mb-4">Ticket #{selectedTicket.id}</h2>

                <div className="flex flex-col gap-4 mb-4">
                  <div>
                    <div className="text-xs uppercase tracking-wide text-gray-400">From</div>
                    <div>{selectedTicket.sender}</div>
                  </div>
                  <div>
                    <div className="text-xs uppercase tracking-wide text-gray-400">Subject</div>
                    <div>{selectedTicket.subject}</div>
                  </div>
                  <div>
                    <div className="text-xs uppercase tracking-wide text-gray-400">Body</div>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{selectedTicket.body}</p>
                  </div>
                  <div>
                    <div className="text-xs uppercase tracking-wide text-gray-400">AI predicted</div>
                    <div>
                      {selectedTicket.category} / {selectedTicket.urgency} ({selectedTicket.confidence} confidence)
                    </div>
                  </div>
                </div>

                <div className="flex gap-4 mb-5">
                  <label className="flex-1 flex flex-col gap-1.5 text-sm text-gray-700">
                    Category
                    <select
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      className="border border-gray-300 rounded-md px-2.5 py-2 text-sm"
                    >
                      <option value="billing">billing</option>
                      <option value="technical">technical</option>
                      <option value="access">access</option>
                      <option value="general">general</option>
                    </select>
                  </label>

                  <label className="flex-1 flex flex-col gap-1.5 text-sm text-gray-700">
                    Urgency
                    <select
                      value={urgency}
                      onChange={(e) => setUrgency(e.target.value)}
                      className="border border-gray-300 rounded-md px-2.5 py-2 text-sm"
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
                    className="bg-indigo-600 text-white font-semibold px-5 py-2.5 rounded-lg hover:bg-indigo-700"
                  >
                    Submit Correction
                  </button>
                  <button
                    onClick={() => setSelectedTicket(null)}
                    className="border border-gray-300 text-gray-700 px-5 py-2.5 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;