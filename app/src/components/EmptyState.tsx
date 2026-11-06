import type { ReactNode } from 'react';

type Props = {
  title: string;
  hint: string;
  action?: ReactNode;
};

export function EmptyState({ title, hint, action }: Props) {
  return (
    <div className="empty-state">
      <div className="empty-state__icon" aria-hidden>
        ◌
      </div>
      <p className="empty-state__title">{title}</p>
      <p className="muted">{hint}</p>
      {action}
    </div>
  );
}
