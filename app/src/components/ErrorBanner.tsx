type Props = {
  message: string;
  onRetry?: () => void;
};

export function ErrorBanner({ message, onRetry }: Props) {
  const navOffline = typeof navigator !== 'undefined' && navigator.onLine === false;
  const diagnostico = navOffline
    ? 'Diagnóstico: o navegador indica falta de internet (offline). Isso é distinto de a API local do OTTO estar parada — mesmo offline, se a API local estiver no ar, dados já gravados neste computador podem carregar.'
    : 'Diagnóstico: há conexão de rede no navegador, mas a API local não respondeu. Inicie o OTTO (INICIAR-OTTO.bat) e tente de novo. Não é necessariamente falta de internet.';
  return (
    <div className="error-banner" role="alert">
      <div>
        <strong>Não foi possível carregar os dados locais</strong>
        <p>{message}</p>
        <p className="muted">{diagnostico}</p>
      </div>
      {onRetry && (
        <button type="button" className="btn btn--ghost" onClick={onRetry}>
          Tentar novamente
        </button>
      )}
    </div>
  );
}
