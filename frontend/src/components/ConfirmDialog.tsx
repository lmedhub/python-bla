import { useEffect, useId, useRef } from "react";
import { userMessage } from "../api/errors";
import styles from "./ConfirmDialog.module.css";

interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel: string;
  pending: boolean;
  error: unknown;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * A modal question, built on the native <dialog>: the browser traps focus inside it,
 * closes it on Esc and makes the page behind it inert. Render it only while it is open.
 */
export function ConfirmDialog(props: ConfirmDialogProps) {
  const { title, message, confirmLabel, pending, error, onConfirm, onCancel } = props;
  const dialog = useRef<HTMLDialogElement>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  const titleId = useId();

  useEffect(() => {
    dialog.current?.showModal();
    // Focus starts on the safe choice, so Enter never deletes by accident.
    cancel.current?.focus();
  }, []);

  return (
    // onClose also fires when the user presses Esc.
    <dialog ref={dialog} aria-labelledby={titleId} className={styles.dialog} onClose={onCancel}>
      <h2 id={titleId}>{title}</h2>
      <p>{message}</p>
      {error !== null && (
        <p role="alert" className={styles.error}>
          {userMessage(error)}
        </p>
      )}
      <div className={styles.actions}>
        <button ref={cancel} type="button" className="secondary" onClick={onCancel}>
          Cancel
        </button>
        <button type="button" className="danger" disabled={pending} onClick={onConfirm}>
          {confirmLabel}
        </button>
      </div>
    </dialog>
  );
}
