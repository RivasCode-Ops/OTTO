export function LoadingSkeleton() {
  return (
    <div className="skeleton-layout" aria-busy="true" aria-label="Carregando radar">
      <div className="kpi-strip">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="kpi-card skeleton-block" />
        ))}
      </div>

      <section className="priority">
        <div className="skeleton-line skeleton-line--title" />
        <div className="priority__grid">
          {[1, 2, 3].map((i) => (
            <div key={i} className="priority-card skeleton-block skeleton-block--tall" />
          ))}
        </div>
      </section>

      <section className="table-section">
        <div className="skeleton-line skeleton-line--title" />
        <div className="skeleton-table">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="skeleton-row" />
          ))}
        </div>
      </section>
    </div>
  );
}
