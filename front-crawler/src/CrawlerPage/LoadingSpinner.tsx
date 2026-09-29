import React from "react";

const LoadingSpinner: React.FC = () => (
  <div style={{ marginTop: "1rem" }}>
    <div className="spinner" />
    <p>Working...</p>
    <style>
      {`
        .spinner {
          width: 24px;
          height: 24px;
          border: 3px solid rgba(0, 0, 0, 0.1);
          border-top-color: #000;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 10px auto;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}
    </style>
  </div>
);

export default LoadingSpinner;
