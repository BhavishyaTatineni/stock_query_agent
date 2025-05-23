import axios from "axios";
import React, { useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL = "https://ukyai7smrnayjgyx5ayw2ium6i0jhufn.lambda-url.us-east-1.on.aws/query";

function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Hello! I am your Stock Query Assistant. Ask me about stock prices or history (e.g., 'What is the current price of Apple stock?')."
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: "user", content: input };
    setMessages((msgs) => [...msgs, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post(API_URL, { text: input });
      setMessages((msgs) => [
        ...msgs,
        { role: "assistant", content: res.data.response }
      ]);
    } catch (err) {
      setMessages((msgs) => [
        ...msgs,
        { role: "assistant", content: "Sorry, there was an error. Please try again." }
      ]);
    }
    setLoading(false);
  };

  return (
    <div className="chatgpt-container">
      <div className="chatgpt-header">Stock Query Chat</div>
      <div className="chatgpt-messages">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`chatgpt-message ${msg.role === "user" ? "user" : "assistant"}`}
          >
            <div className="chatgpt-bubble">{msg.content}</div>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>
      <form className="chatgpt-input-row" onSubmit={handleSend}>
        <input
          className="chatgpt-input"
          type="text"
          placeholder="Type your stock question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button className="chatgpt-send" type="submit" disabled={loading || !input.trim()}>
          {loading ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}

export default App;