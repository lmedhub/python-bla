import styles from "./Pagination.module.css";

interface PaginationProps {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
}

export function Pagination({ page, totalPages, onChange }: PaginationProps) {
  return (
    <nav aria-label="Pagination" className={styles.pagination}>
      <button
        type="button"
        className="secondary"
        aria-label="Previous page"
        disabled={page <= 1}
        onClick={() => {
          onChange(page - 1);
        }}
      >
        ← Previous
      </button>
      <span>
        Page {page} of {totalPages}
      </span>
      <button
        type="button"
        className="secondary"
        aria-label="Next page"
        disabled={page >= totalPages}
        onClick={() => {
          onChange(page + 1);
        }}
      >
        Next →
      </button>
    </nav>
  );
}
