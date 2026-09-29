import React, { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
} from "@mui/material";

interface Props {
  open: boolean;
  onClose: () => void;
  onSave: (entries: string[]) => void;
}

const AdsTxtModal: React.FC<Props> = ({ open, onClose, onSave }) => {
  const [inputValue, setInputValue] = useState<string>("");
  const [error, setError] = useState<string>("");

  const handleSave = () => {
    const lines = inputValue
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);

    if (lines.length === 0) {
      setError("Please enter at least one valid line.");
      return;
    }

    setError("");
    onSave(lines);
    onClose();
    setInputValue("");
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add ads.txt values to check</DialogTitle>
      <DialogContent>
        <Typography variant="body2" gutterBottom>
          Paste each ads.txt entry on a new line:
        </Typography>
        <TextField
          multiline
          fullWidth
          minRows={6}
          placeholder="e.g. rubiconproject.com, 10278, RESELLER, 0bfd66d529a55807"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
        />
        {error && (
          <Typography variant="caption" color="error">
            {error}
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSave}>
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AdsTxtModal;
