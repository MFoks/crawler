import React from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Box,
  Chip,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import CancelOutlinedIcon from "@mui/icons-material/CancelOutlined";

interface DeviceLogs {
  desktop?: string[];
  mobile?: string[];
}

interface FeedbackModalProps {
  open: boolean;
  onClose: () => void;
  adsTxtEntries: string[];
  crawlerFeedback: {
    logsFeedback: {
      homePage?: string[] | DeviceLogs;
      subPage?: string[] | DeviceLogs;
    };
    adnginModules?: Record<string, any>;
    diagnostics?: {
      cmp?: string | null;
      tcfStringValid?: boolean | null;
      adnginExperimentEnabled?: boolean | null;
    };
  };
}

const FeedbackModal: React.FC<FeedbackModalProps> = ({
  open,
  onClose,
  adsTxtEntries,
  crawlerFeedback,
}) => {
  const { logsFeedback = {}, adnginModules = {}, diagnostics = {} } = crawlerFeedback || {};

  const renderModuleStatus = () => {
    if (!adnginModules || typeof adnginModules !== 'object') return null;
    return Object.entries(adnginModules).map(([name, config]) => {
      const enabled = config?.enabled;
      const label = name.charAt(0).toUpperCase() + name.slice(1);
      return (
        <Box key={name} display="flex" alignItems="center" gap={1} mb={1}>
          {enabled ? (
            <CheckCircleOutlineIcon color="success" />
          ) : (
            <CancelOutlinedIcon color="error" />
          )}
          <Typography variant="body1">
            {label} – {enabled ? "enabled" : "disabled"}
          </Typography>
        </Box>
      );
    });
  };

  // Helper function to normalize logs (handle both old string[] and new {desktop, mobile} format)
  const normalizeLogs = (logs: string[] | DeviceLogs | undefined): string[] => {
    if (!logs) return [];
    if (Array.isArray(logs)) return logs;
    // New format: {desktop: [], mobile: []}
    const result: string[] = [];
    if (logs.desktop && Array.isArray(logs.desktop)) {
      logs.desktop.forEach(log => result.push(`[Desktop] ${log}`));
    }
    if (logs.mobile && Array.isArray(logs.mobile)) {
      logs.mobile.forEach(log => result.push(`[Mobile] ${log}`));
    }
    return result;
  };

  const renderLogs = (title: string, logs?: string[] | DeviceLogs) => {
    const normalizedLogs = normalizeLogs(logs);
    if (normalizedLogs.length === 0) return null;
    return (
      <Accordion sx={{ mt: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>
            {title} ({normalizedLogs.length})
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          {normalizedLogs.map((line, idx) => (
            <Typography key={idx} variant="body2" gutterBottom>
              {line}
            </Typography>
          ))}
        </AccordionDetails>
      </Accordion>
    );
  };

  const renderDiagnostics = () => {
    if (!diagnostics) return null;
    const { cmp, tcfStringValid, adnginExperimentEnabled } = diagnostics;
    if (!cmp && tcfStringValid === null && adnginExperimentEnabled === null) return null;

    return (
      <Accordion sx={{ mt: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Diagnostics</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" gutterBottom>
            CMP: {cmp || "Not detected"}
          </Typography>
          <Typography variant="body2" gutterBottom>
            TCF String Valid: {tcfStringValid === true
              ? "Yes"
              : tcfStringValid === false
              ? "No"
              : "Unknown"}
          </Typography>
          <Typography variant="body2" gutterBottom>
            Adngin Experiment Enabled: {adnginExperimentEnabled === true
              ? "Yes"
              : adnginExperimentEnabled === false
              ? "No"
              : "Unknown"}
          </Typography>
        </AccordionDetails>
      </Accordion>
    );
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Feedback Summary</DialogTitle>
      <DialogContent dividers>
        {/* Adngin Modules ALWAYS FIRST */}
        {adnginModules && Object.keys(adnginModules).length > 0 && (
          <Accordion sx={{ mt: 0 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>Adngin Modules</Typography>
            </AccordionSummary>
            <AccordionDetails>{renderModuleStatus()}</AccordionDetails>
          </Accordion>
        )}

        {/* ads.txt entries */}
        {adsTxtEntries && adsTxtEntries.length > 0 && (
          <Accordion sx={{ mt: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>ads.txt – missing entries ({adsTxtEntries.length})</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {adsTxtEntries.map((entry, idx) => (
                <Typography key={idx} variant="body2" gutterBottom>
                  {entry}
                </Typography>
              ))}
            </AccordionDetails>
          </Accordion>
        )}

        {/* Logs */}
        {renderLogs("Logs: Homepage", logsFeedback?.homePage)}
        {renderLogs("Logs: Subpage", logsFeedback?.subPage)}

        {/* Diagnostics */}
        {renderDiagnostics()}
      </DialogContent>

      <Box display="flex" justifyContent="flex-end" p={2}>
        <Chip label="Close" onClick={onClose} clickable />
      </Box>
    </Dialog>
  );
};

export default FeedbackModal;
