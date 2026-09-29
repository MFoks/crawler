import React from "react";

interface Props {
  homepage: string;
  article: string;
  setHomepage: (value: string) => void;
  setArticle: (value: string) => void;
  onSubmit: () => void;
}

const DomainInput: React.FC<Props> = ({
  homepage,
  article,
  setHomepage,
  setArticle,
  onSubmit,
}) => (
  <div>
    <input
      type="text"
      value={homepage}
      onChange={(e) => setHomepage(e.target.value)}
      placeholder="Strona główna (e.g. tftacademy.com)"
      style={{ padding: "8px", width: "300px", marginRight: "10px" }}
    />
    <input
      type="text"
      value={article}
      onChange={(e) => setArticle(e.target.value)}
      placeholder="Strona artykułu (opcjonalnie)"
      style={{ padding: "8px", width: "300px", marginRight: "10px" }}
    />
    <button onClick={onSubmit}>Run Crawler</button>
  </div>
);

export default DomainInput;