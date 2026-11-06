import type { AlertasResposta } from '../types';

type Props = {
  alertas: AlertasResposta | null;
  onDismiss: () => void;
  onSelect: (numero: string) => void;
  onEnableNotify?: () => void;
  notifyEnabled: boolean;
};

export function AlertsBanner({ alertas, onDismiss, onSelect, onEnableNotify, notifyEnabled }: Props) {
  if (!alertas) return null;

  const temSinal =
    alertas.novas_alta_confianca > 0 ||
    alertas.mudancas_7d > 0 ||
    alertas.vencendo_urgente_3d > 0;

  if (!temSinal) return null;

  const partes: string[] = [];
  if (alertas.novas_alta_confianca > 0) {
    partes.push(
      `${alertas.novas_alta_confianca} nova(s) TI alta confiança`,
    );
  }
  if (alertas.mudancas_7d > 0) {
    partes.push(`${alertas.mudancas_7d} mudança(s) recente(s)`);
  }
  if (alertas.vencendo_urgente_3d > 0) {
    partes.push(`${alertas.vencendo_urgente_3d} vence(m) em ≤3 dias`);
  }

  return (
    <div className="alerts-banner" role="status">
      <div className="alerts-banner__body">
        <strong>Alertas ativos</strong>
        <p>{partes.join(' · ')}</p>
        {alertas.items.length > 0 && (
          <ul className="alerts-banner__list">
            {alertas.items.slice(0, 3).map((item) => (
              <li key={`${item.tipo}-${item.numero_controle_pncp}`}>
                <button type="button" onClick={() => onSelect(item.numero_controle_pncp)}>
                  [{item.tipo}] {item.orgao_razao_social?.slice(0, 36) ?? item.numero_controle_pncp}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="alerts-banner__actions">
        {!notifyEnabled && onEnableNotify && typeof Notification !== 'undefined' && (
          <button type="button" className="btn btn--ghost" onClick={onEnableNotify}>
            Ativar notificações
          </button>
        )}
        <button type="button" className="btn btn--ghost" onClick={onDismiss}>
          Marcar como visto
        </button>
      </div>
    </div>
  );
}
