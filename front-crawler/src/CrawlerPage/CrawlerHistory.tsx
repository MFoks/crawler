import React from "react";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  List,
  ListItem,
  ListItemText,
} from "@mui/material";

interface HistoryEntry {
  timestamp: string;
  domain: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  history: HistoryEntry[];
}

const CrawlerHistoryModal: React.FC<Props> = ({ open, onClose, history }) => {
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Recent Crawls</DialogTitle>
      <DialogContent>
        <List>
          {history.length === 0 ? (
            <ListItem>
              <ListItemText primary="No history yet." />
            </ListItem>
          ) : (
            history.map((entry, index) => (
              <ListItem key={index} divider>
                <ListItemText
                  primary={`[${entry.timestamp}]`}
                  secondary={entry.domain}
                />
              </ListItem>
            ))
          )}
        </List>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} variant="outlined">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CrawlerHistoryModal;