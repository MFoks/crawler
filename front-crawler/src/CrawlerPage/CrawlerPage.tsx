import React, { useState, useEffect, useRef } from "react";
import CrawlerHistoryModal from "./CrawlerHistory";
import ExecutionLogs from "./ExecutionLogs";
import AdsTxtPopUp from "./AdsTxTPopUp";
import FeedbackModal from "./FeedbackModal";
import { apiGet, apiPost, logout } from "../api";
import { useNavigate } from "react-router-dom";

import {
  Box,
  Button,
  CircularProgress,
  Container,
  Paper,
  TextField,
  Typography,
  Chip,
} from "@mui/material";

interface HistoryEntry {
  timestamp: string;
  domain: string;
}

interface CrawlerFeedback {
  logsFeedback: {
    homePage?: string[];
    subPage?: string[];
  };
  adnginModules?: Record<string, any>;
  diagnostics?: {
    cmp?: string | null;
    tcfStringValid?: boolean | null;
    adnginExperimentEnabled?: boolean | null;
  };
}

interface QueueStatus {
  active_count: number;
  queue_size: number;
  max_concurrent: number;
}

const CrawlerPage: React.FC = () => {
  const navigate = useNavigate();
  const [homepage, setHomepage] = useState<string>("");
  const [article, setArticle] = useState<string>("");
  const [adsEntries, setAdsEntries] = useState<string[]>([]);
  const [showAdsModal, setShowAdsModal] = useState<boolean>(false);
  const [showFeedback, setShowFeedback] = useState<boolean>(false);
  const [missingAdsEntries, setMissingAdsEntries] = useState<string[]>([]);
  const [crawlerFeedback, setCrawlerFeedback] = useState<CrawlerFeedback>({
    logsFeedback: {},
    adnginModules: {},
    diagnostics: {},
  });
  const [status, setStatus] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isCompleted, setIsCompleted] = useState<boolean>(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [showHistory, setShowHistory] = useState<boolean>(false);
  const [queueStatus, setQueueStatus] = useState<QueueStatus | null>(null);

  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const logsRef = useRef<NodeJS.Timeout | null>(null);
  const queueRef = useRef<NodeJS.Timeout | null>(null);
  const historyButtonRef = useRef<HTMLButtonElement>(null);

  // Load history on mount
  useEffect(() => {
    apiGet("/api/history")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) setHistory(data);
        else setHistory([]);
      })
      .catch(() => setHistory([]));
  }, []);

  // Poll queue status
  useEffect(() => {
    const fetchQueueStatus = async () => {
      try {
        const res = await apiGet("/api/queue-status");
        if (res.ok) {
          const data = await res.json();
          setQueueStatus(data);
        }
      } catch (e) {
        console.warn("Failed to fetch queue status", e);
      }
    };

    fetchQueueStatus();
    queueRef.current = setInterval(fetchQueueStatus, 5000);

    return () => {
      if (queueRef.current) clearInterval(queueRef.current);
    };
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  // Add local log message (shown immediately)
  const addLocalLog = (message: string) => {
    setLogs((prev) => [...prev, message]);
  };

  const handleRunCrawler = async () => {
    if (!homepage) {
      setStatus("❗ Please enter a homepage before starting.");
      return;
    }

    const timestamp = new Date().toLocaleString();

    try {
      await apiPost("/api/history", { timestamp, domain: homepage });
      setHistory((prev) => [{ timestamp, domain: homepage }, ...prev.slice(0, 49)]);
    } catch (e) {
      console.warn("Failed to update history", e);
    }

    setStatus("🔄 Starting crawler...");
    setIsLoading(true);
    setIsCompleted(false);
    setLogs([]);
    setMissingAdsEntries([]);
    setCrawlerFeedback({ logsFeedback: {}, adnginModules: {}, diagnostics: {} });

    // Immediate local feedback
    addLocalLog("🔄 Connecting to crawler service...");

    try {
      const res = await apiPost("/api/trigger-crawler", { homepage, article, adsEntries });
      
      if (res.status === 401) {
        logout();
        navigate("/login");
        return;
      }

      const data = await res.json();
      
      if (data.queue_position > 0) {
        setStatus(`📋 Queued (position: ${data.queue_position}, active: ${data.active_crawlers}/${data.max_concurrent})`);
        addLocalLog(`📋 Added to queue (position: ${data.queue_position})`);
        addLocalLog(`⏳ Waiting for available slot (${data.active_crawlers}/${data.max_concurrent} running)...`);
      } else {
        setStatus("🚀 Crawler started!");
        addLocalLog("✅ Request accepted");
        addLocalLog("⏳ Initializing crawler...");
      }

      startPolling();
      startLogPolling();
    } catch (error) {
      setStatus("❌ Error while triggering the crawler.");
      addLocalLog("❌ Failed to connect to crawler service");
      setIsLoading(false);
    }
  };

  const startPolling = () => {
    if (pollingRef.current) clearInterval(pollingRef.current);

    pollingRef.current = setInterval(async () => {
      const res = await apiGet(`/api/crawler-status?domain=${homepage}`);
      
      if (res.status === 401) {
        logout();
        navigate("/login");
        return;
      }
      
      const data = await res.json();

      if (data.status === "done") {
        setStatus("✅ Crawler has completed its work!");
        setIsLoading(false);
        setIsCompleted(true);
        clearInterval(pollingRef.current!);
        clearInterval(logsRef.current!);

        try {
          const res = await apiGet(`/api/crawler-feedback?domain=${homepage}`);
          const data = await res.json();
          if (typeof data.crawlerFeedback === "object") {
            setCrawlerFeedback(data.crawlerFeedback);
          }
          if (Array.isArray(data.adsTxtEntries)) {
            setMissingAdsEntries(data.adsTxtEntries);
          }
        } catch (e) {
          console.warn("Failed to load crawler feedback:", e);
        }
      } else if (data.status === "pending") {
        if (data.is_active) {
          setStatus("⏳ Crawler is running...");
        } else {
          setStatus(`📋 Waiting in queue (${data.queue_size} in queue, ${data.active_crawlers} running)`);
        }
      }
    }, 5000);
  };

  const startLogPolling = () => {
    if (logsRef.current) clearInterval(logsRef.current);

    // Start polling faster initially, then slow down
    let pollCount = 0;
    const pollLogs = async () => {
      const res = await apiGet(`/api/crawler-logs?domain=${homepage}`);
      
      if (res.status === 401) {
        logout();
        navigate("/login");
        return;
      }
      
      const data = await res.json();
      const allLogs = data.logs || [];
      
      if (allLogs.length > 0) {
        const cleanedLogs = allLogs.map((log: string) =>
          log.replace(/^(homePageDesktop|homePageMobile|subPageDesktop|subPageMobile|adsTxt|system),\s?/, "")
        );
        setLogs(cleanedLogs);
      }
      
      pollCount++;
    };

    // Poll immediately
    pollLogs();

    // Then poll every 2 seconds (faster feedback)
    logsRef.current = setInterval(pollLogs, 2000);
  };

  const handleDownloadCSV = async () => {
    try {
      const response = await apiGet(`/api/download-logs?domain=${homepage}`);
      
      if (response.status === 401) {
        logout();
        navigate("/login");
        return;
      }
      
      if (!response.ok) throw new Error("Failed to fetch CSV");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = `${homepage}_log.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("CSV download error:", err);
      alert("Failed to download CSV");
    }
  };

  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
      if (logsRef.current) clearInterval(logsRef.current);
    };
  }, []);

  return (
    <Container maxWidth="md" sx={{ mt: 6 }}>
      <Paper elevation={3} sx={{ px: 4, py: 4, pt: "10px" }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
          <Box flex="1" sx={{ pr: 2 }}>
            <Typography variant="h4" sx={{ mb: 0.5 }}>
              Crawler Page
            </Typography>
            <Typography variant="body1" sx={{ mb: 0 }}>
              Enter a homepage and optional article to start the crawler.
            </Typography>
          </Box>

          <Box display="flex" flexDirection="column" alignItems="flex-end" gap={1}>
            <Box
              component="img"
              src="/images/snigel_logo_2.png"
              alt="Snigel Logo"
              sx={{
                height: 120,
                width: "auto",
                objectFit: "contain",
              }}
            />
            <Button 
              variant="text" 
              size="small" 
              onClick={handleLogout}
              sx={{ color: '#666' }}
            >
              Logout
            </Button>
          </Box>
        </Box>

        {/* Queue Status */}
        {queueStatus && (
          <Box display="flex" gap={1} mb={2}>
            <Chip 
              label={`Active: ${queueStatus.active_count}/${queueStatus.max_concurrent}`} 
              color={queueStatus.active_count >= queueStatus.max_concurrent ? "warning" : "success"}
              size="small"
            />
            {queueStatus.queue_size > 0 && (
              <Chip 
                label={`Queue: ${queueStatus.queue_size}`} 
                color="info"
                size="small"
              />
            )}
          </Box>
        )}

        <Box display="flex" gap={2} mb={2}>
          <Button variant="outlined" onClick={() => setShowHistory(true)} ref={historyButtonRef}>
            Show History
          </Button>
          <Button variant="outlined" onClick={() => setShowAdsModal(true)}>
            Add ads.txt entries {adsEntries.length > 0 && `✅ (${adsEntries.length})`}
          </Button>
        </Box>

        <Box display="flex" flexDirection="column" gap={2} mb={2}>
          <TextField
            fullWidth
            variant="outlined"
            label="Main Page/Home page"
            value={homepage}
            onChange={(e) => setHomepage(e.target.value)}
          />
          <TextField
            fullWidth
            variant="outlined"
            label="Article page (optional)"
            value={article}
            onChange={(e) => setArticle(e.target.value)}
          />
          <Button 
            variant="contained" 
            onClick={handleRunCrawler}
            disabled={isLoading}
          >
            {isLoading ? "Running..." : "Run"}
          </Button>
        </Box>

        {status && (
          <Typography variant="body2" sx={{ mt: 1 }}>
            {status}
          </Typography>
        )}

        {isLoading && (
          <Box display="flex" alignItems="center" gap={1} mt={2}>
            <CircularProgress size={20} />
            <Typography variant="body2">Working...</Typography>
          </Box>
        )}

        {isCompleted && logs.length > 0 && (
          <Box mt={3} display="flex" gap={2}>
            <Button variant="outlined" onClick={handleDownloadCSV}>
              Download CSV
            </Button>
            <Button
              variant="outlined"
              color={
                missingAdsEntries.length > 0 ||
                Object.values(crawlerFeedback.logsFeedback || {}).some(
                  (list) => list && list.length > 0
                )
                  ? "warning"
                  : "success"
              }
              onClick={() => setShowFeedback(true)}
            >
              Feedback
            </Button>
          </Box>
        )}

        <ExecutionLogs logs={logs} />

        {isCompleted && crawlerFeedback.diagnostics && (
          <Box mt={3}>
            <Typography variant="h6" gutterBottom>
              Diagnostics
            </Typography>
            <Typography variant="body2">
              CMP: {crawlerFeedback.diagnostics.cmp || "Not detected"}
            </Typography>
            <Typography variant="body2">
              TCF String Valid: {crawlerFeedback.diagnostics.tcfStringValid === true
                ? "Yes"
                : crawlerFeedback.diagnostics.tcfStringValid === false
                ? "No"
                : "Unknown"}
            </Typography>
            <Typography variant="body2">
              Adngin Experiment Enabled: {crawlerFeedback.diagnostics.adnginExperimentEnabled === true
                ? "Yes"
                : crawlerFeedback.diagnostics.adnginExperimentEnabled === false
                ? "No"
                : "Unknown"}
            </Typography>
          </Box>
        )}
      </Paper>

      <CrawlerHistoryModal
        open={showHistory}
        onClose={() => {
          setShowHistory(false);
          setTimeout(() => {
            historyButtonRef.current?.focus();
          }, 0);
        }}
        history={history}
      />

      <AdsTxtPopUp
        open={showAdsModal}
        onClose={() => setShowAdsModal(false)}
        onSave={(entries) => setAdsEntries(entries)}
      />

      <FeedbackModal
        open={showFeedback}
        onClose={() => setShowFeedback(false)}
        adsTxtEntries={missingAdsEntries}
        crawlerFeedback={crawlerFeedback}
      />
    </Container>
  );
};

export default CrawlerPage;
