import React from "react";

const StatusMessage: React.FC<{ status: string | null }> = ({ status }) =>
  status ? <p style={{ marginTop: "1rem" }}>{status}</p> : null;

export default StatusMessage;
