import React, { useState, useEffect } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown"; // ← Add this import
import "./App.css";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [apiHealth, setApiHealth] = useState(null);
  const [documentCount, setDocumentCount] = useState(0);
  const [expandedSources, setExpandedSources] = useState({}); // Track which sources are expanded

  useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`);
      setApiHealth(response.data);
      setDocumentCount(response.data.documents_count || 0);
    } catch (error) {
      console.error("API health check failed:", error);
      setApiHealth({ status: "unhealthy" });
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = { type: "user", content: inputMessage };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        query: inputMessage,
      });

      const botMessage = {
        type: "bot",
        content: response.data.answer,
        sources: response.data.sources || [],
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        type: "bot",
        content:
          "Sorry, I encountered an error while processing your request. Make sure you have added some documents to the knowledge base.",
        error: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    }

    setInputMessage("");
    setIsLoading(false);
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setIsLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      alert(`Successfully uploaded: ${response.data.message}`);
      checkApiHealth(); // Refresh document count
    } catch (error) {
      alert(`Upload failed: ${error.response?.data?.detail || error.message}`);
    }
    setIsLoading(false);
    event.target.value = ""; // Reset file input
  };

  const addSampleText = async () => {
    const sampleText = `
    Artificial Intelligence Policy Framework

    Key principles for AI governance:
    1. Transparency: AI systems should be explainable and auditable
    2. Fairness: AI should not discriminate against individuals or groups
    3. Privacy: Personal data should be protected in AI systems
    4. Safety: AI systems should be tested for potential risks
    5. Accountability: Clear responsibility for AI decisions should be established

    Regulatory approaches include:
    - Risk-based frameworks that categorize AI systems by potential harm
    - Sector-specific regulations for high-risk applications
    - International cooperation on AI standards and best practices
    - Regular audits and compliance monitoring

    Current challenges in AI policy include balancing innovation with protection,
    addressing algorithmic bias, and ensuring human oversight of automated decisions.
    `;

    setIsLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/add_text`, {
        text: sampleText,
        metadata: { source: "AI Policy Framework Sample" },
      });

      alert(`Sample text added: ${response.data.message}`);
      checkApiHealth(); // Refresh document count
    } catch (error) {
      alert(
        `Failed to add text: ${error.response?.data?.detail || error.message}`
      );
    }
    setIsLoading(false);
  };

  const toggleSources = (messageIndex) => {
    setExpandedSources((prev) => ({
      ...prev,
      [messageIndex]: !prev[messageIndex],
    }));
  };

  const clearMemory = async () => {
    try {
      await axios.delete(`${API_BASE_URL}/clear_memory`);
      setMessages([]);
      alert("Chat memory cleared");
    } catch (error) {
      alert(
        `Failed to clear memory: ${
          error.response?.data?.detail || error.message
        }`
      );
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>AI Policy Analysis Chatbot</h1>
        <div className="status-bar">
          <span
            className={`status ${
              apiHealth?.status === "healthy" ? "healthy" : "unhealthy"
            }`}
          >
            API: {apiHealth?.status || "checking..."}
          </span>
          <span className="doc-count">Documents: {documentCount}</span>
        </div>
      </header>

      <div className="main-container">
        <div className="sidebar">
          <div className="upload-section">
            <h3>Upload Documents</h3>
            <input
              type="file"
              accept=".pdf,.txt,.md"
              onChange={handleFileUpload}
              disabled={isLoading}
            />
            <button onClick={addSampleText} disabled={isLoading}>
              Add Sample AI Policy Text
            </button>
          </div>

          <div className="controls">
            <button onClick={checkApiHealth} disabled={isLoading}>
              Check API Status
            </button>
            <button onClick={clearMemory} disabled={isLoading}>
              Clear Chat Memory
            </button>
          </div>
        </div>

        <div className="chat-container">
          <div className="messages">
            {messages.length === 0 && (
              <div className="welcome-message">
                <p>
                  Welcome! Start by uploading some documents or adding sample
                  text, then ask me questions about AI policy.
                </p>
              </div>
            )}
            {messages.map((message, index) => (
              <div
                key={index}
                className={`message ${message.type} ${
                  message.error ? "error" : ""
                }`}
              >
                <div className="message-content">
                  {/* 🎯 THIS IS THE KEY CHANGE - Use ReactMarkdown for bot messages */}
                  {message.type === "bot" ? (
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  ) : (
                    message.content
                  )}
                </div>
                {message.sources && message.sources.length > 0 && (
                  <div className="sources">
                    <div
                      className="sources-header"
                      onClick={() => toggleSources(index)}
                    >
                      <strong>Sources ({message.sources.length})</strong>
                      <button className="sources-toggle">
                        {expandedSources[index] ? "Hide ▲" : "Show ▼"}
                      </button>
                    </div>
                    {expandedSources[index] && (
                      <div className="sources-content">
                        {message.sources.map((source, idx) => (
                          <div key={idx} className="source">
                            <small>
                              <strong>
                                {source.metadata.source || `Source ${idx + 1}`}:
                              </strong>
                              <br />
                              {source.content}
                              {source.similarity_score && (
                                <span
                                  style={{ color: "#888", fontSize: "11px" }}
                                >
                                  {" "}
                                  (Relevance:{" "}
                                  {(source.similarity_score * 100).toFixed(1)}%)
                                </span>
                              )}
                            </small>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="message bot loading">
                <div className="typing-indicator">Thinking...</div>
              </div>
            )}
          </div>

          <div className="input-container">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about AI policy..."
              disabled={isLoading}
              rows="3"
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !inputMessage.trim()}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
