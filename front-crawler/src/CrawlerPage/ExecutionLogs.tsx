import React from "react";

const ExecutionLogs: React.FC<{ logs: string[] }> = ({ logs }) =>
  logs.length > 0 ? (
    <div style={{ marginTop: "2rem" }}>
      <h3>Execution Logs:</h3>
      <pre style={{
        background: "#f4f4f4",
        padding: "1rem",
        overflowX: "auto",
        whiteSpace: "pre-wrap",
        wordBreak: "break-word"
      }}>
        {logs.join("\n")}
      </pre>
    </div>
  ) : null;

export default ExecutionLogs;
